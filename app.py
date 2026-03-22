from flask import Flask, request, jsonify
from PyPDF2 import PdfReader, PdfWriter
import io
import base64
import os

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "service": "PDF Splitter API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "split": "/split-pdf (POST)"
        }
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "service": "PDF Splitter API"
    })

@app.route('/split-pdf', methods=['POST'])
def split_pdf():
    try:
        # Récupérer les données
        data = request.json
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        pdf_base64 = data.get('pdf')
        text_array = data.get('text_array', [])
        
        if not pdf_base64:
            return jsonify({"error": "Missing 'pdf' field in request body"}), 400
        
        # Décoder le PDF
        try:
            pdf_bytes = base64.b64decode(pdf_base64)
        except Exception as e:
            return jsonify({"error": f"Invalid base64 PDF data: {str(e)}"}), 400
        
        # Lire le PDF
        pdf_reader = PdfReader(io.BytesIO(pdf_bytes))
        total_pages = len(pdf_reader.pages)
        
        # Détecter les pages blanches
        blank_pages = []
        
        if text_array and len(text_array) == total_pages:
            # Utiliser le texte fourni par pdf-parse (plus rapide)
            for i, text in enumerate(text_array):
                if len(text.strip()) < 10:
                    blank_pages.append(i)
        else:
            # Extraire le texte nous-mêmes
            for i in range(total_pages):
                page = pdf_reader.pages[i]
                text = page.extract_text().strip()
                if len(text) < 10:
                    blank_pages.append(i)
        
        # Créer les groupes de pages (documents)
        document_groups = []
        current_group = []
        
        for i in range(total_pages):
            if i in blank_pages:
                # Page blanche trouvée
                if current_group:
                    document_groups.append({
                        'start_page': current_group[0],
                        'end_page': current_group[-1],
                        'pages': current_group
                    })
                    current_group = []
            else:
                # Page avec contenu
                current_group.append(i)
        
        # Ne pas oublier le dernier groupe
        if current_group:
            document_groups.append({
                'start_page': current_group[0],
                'end_page': current_group[-1],
                'pages': current_group
            })
        
        # Créer les PDFs individuels
        split_documents = []
        
        for idx, group in enumerate(document_groups):
            pdf_writer = PdfWriter()
            
            # Ajouter les pages du groupe
            for page_num in group['pages']:
                pdf_writer.add_page(pdf_reader.pages[page_num])
            
            # Convertir en bytes
            output = io.BytesIO()
            pdf_writer.write(output)
            output.seek(0)
            
            split_documents.append({
                'document_number': idx + 1,
                'page_count': len(group['pages']),
                'start_page': group['start_page'] + 1,  # +1 pour affichage humain
                'end_page': group['end_page'] + 1,
                'file_name': f"mail_{idx + 1}_pages_{group['start_page'] + 1}-{group['end_page'] + 1}.pdf",
                'pdf': base64.b64encode(output.read()).decode('utf-8')
            })
        
        # Retourner la réponse
        return jsonify({
            'success': True,
            'total_pages': total_pages,
            'blank_pages': [p + 1 for p in blank_pages],
            'documents_count': len(split_documents),
            'documents': split_documents
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    # Pour Render, Railway, etc.
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
