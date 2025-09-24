#!/usr/bin/env python3
"""
Script para descargar los recursos necesarios de NLTK
"""

import nltk
import ssl
import os

def download_nltk_resources():
    """Descarga los recursos necesarios de NLTK"""
    
    # Configurar SSL para evitar problemas de certificados
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        pass
    else:
        ssl._create_default_https_context = _create_unverified_https_context
    
    # Lista de recursos necesarios
    resources = [
        'punkt',
        'punkt_tab',
        'stopwords',
        'wordnet',
        'averaged_perceptron_tagger',
        'vader_sentiment',
        'omw-1.4'
    ]
    
    print("Descargando recursos de NLTK...")
    
    for resource in resources:
        try:
            print(f"Descargando {resource}...")
            nltk.download(resource, quiet=False)
            print(f"✓ {resource} descargado correctamente")
        except Exception as e:
            print(f"✗ Error descargando {resource}: {e}")
            # Intentar descargar todo el paquete
            try:
                nltk.download('all', quiet=True)
                print("✓ Descarga completa de NLTK realizada")
                break
            except Exception as e2:
                print(f"✗ Error en descarga completa: {e2}")
    
    print("\nVerificando instalación...")
    
    # Verificar que los recursos están disponibles
    try:
        from nltk.tokenize import sent_tokenize, word_tokenize
        from nltk.corpus import stopwords
        
        # Probar tokenización
        test_text = "Hola mundo. Este es un test."
        sentences = sent_tokenize(test_text)
        words = word_tokenize(test_text)
        
        print(f"✓ Tokenización funciona correctamente")
        print(f"  Oraciones: {sentences}")
        print(f"  Palabras: {words}")
        
        # Probar stopwords
        stop_words = stopwords.words('english')
        print(f"✓ Stopwords cargadas: {len(stop_words)} palabras")
        
    except Exception as e:
        print(f"✗ Error en verificación: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = download_nltk_resources()
    if success:
        print("\n🎉 Todos los recursos de NLTK se han instalado correctamente!")
    else:
        print("\n❌ Hubo problemas instalando algunos recursos de NLTK")
