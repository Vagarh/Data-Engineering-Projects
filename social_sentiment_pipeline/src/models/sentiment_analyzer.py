"""
Analizador de Sentimientos usando modelos pre-entrenados de Transformers
"""
import logging
from typing import Dict, List, Tuple
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    def __init__(self, model_name: str = "cardiffnlp/twitter-roberta-base-sentiment-latest"):
        """
        Inicializar analizador de sentimientos
        
        Args:
            model_name: Nombre del modelo pre-entrenado de HuggingFace
        """
        self.model_name = model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Usando dispositivo: {self.device}")
        
        # Cargar modelo y tokenizer
        self._load_model()
        
        # Mapeo de labels
        self.label_mapping = {
            'LABEL_0': 'negative',
            'LABEL_1': 'neutral', 
            'LABEL_2': 'positive'
        }
    
    def _load_model(self):
        """Cargar modelo y tokenizer"""
        try:
            logger.info(f"Cargando modelo: {self.model_name}")
            
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            
            # Crear pipeline
            self.sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if self.device == "cuda" else -1,
                return_all_scores=True
            )
            
            logger.info("Modelo cargado exitosamente")
            
        except Exception as e:
            logger.error(f"Error cargando modelo: {e}")
            raise
    
    def preprocess_text(self, text: str) -> str:
        """
        Preprocesar texto para análisis de sentimientos
        
        Args:
            text: Texto original del tweet
            
        Returns:
            Texto preprocesado
        """
        # Remover URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        
        # Remover menciones y hashtags (opcional, mantener para contexto)
        # text = re.sub(r'@\w+|#\w+', '', text)
        
        # Remover caracteres especiales excesivos
        text = re.sub(r'[^\w\s@#]', ' ', text)
        
        # Normalizar espacios
        text = ' '.join(text.split())
        
        return text.strip()
    
    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """
        Analizar sentimiento de un texto
        
        Args:
            text: Texto a analizar
            
        Returns:
            Diccionario con scores de sentimiento
        """
        try:
            # Preprocesar texto
            processed_text = self.preprocess_text(text)
            
            if not processed_text:
                return {
                    'positive': 0.33,
                    'neutral': 0.34,
                    'negative': 0.33,
                    'predicted_sentiment': 'neutral',
                    'confidence': 0.34
                }
            
            # Truncar texto si es muy largo
            if len(processed_text) > 512:
                processed_text = processed_text[:512]
            
            # Obtener predicciones
            results = self.sentiment_pipeline(processed_text)
            
            # Procesar resultados
            scores = {}
            for result in results[0]:  # results[0] porque return_all_scores=True
                label = result['label']
                score = result['score']
                
                # Mapear label si es necesario
                if label in self.label_mapping:
                    sentiment = self.label_mapping[label]
                else:
                    sentiment = label.lower()
                
                scores[sentiment] = score
            
            # Determinar sentimiento predicho
            predicted_sentiment = max(scores, key=scores.get)
            confidence = scores[predicted_sentiment]
            
            return {
                **scores,
                'predicted_sentiment': predicted_sentiment,
                'confidence': confidence
            }
            
        except Exception as e:
            logger.error(f"Error analizando sentimiento: {e}")
            # Retornar valores neutros en caso de error
            return {
                'positive': 0.33,
                'neutral': 0.34,
                'negative': 0.33,
                'predicted_sentiment': 'neutral',
                'confidence': 0.34
            }
    
    def analyze_batch(self, texts: List[str]) -> List[Dict[str, float]]:
        """
        Analizar sentimientos de múltiples textos en batch
        
        Args:
            texts: Lista de textos a analizar
            
        Returns:
            Lista de diccionarios con scores de sentimiento
        """
        results = []
        
        for text in texts:
            result = self.analyze_sentiment(text)
            results.append(result)
        
        return results
    
    def get_model_info(self) -> Dict[str, str]:
        """Obtener información del modelo"""
        return {
            'model_name': self.model_name,
            'device': self.device,
            'tokenizer_vocab_size': len(self.tokenizer.vocab) if hasattr(self.tokenizer, 'vocab') else 'unknown'
        }


# Función de utilidad para uso directo
def analyze_text_sentiment(text: str, model_name: str = None) -> Dict[str, float]:
    """
    Función de utilidad para analizar sentimiento de un texto
    
    Args:
        text: Texto a analizar
        model_name: Nombre del modelo (opcional)
        
    Returns:
        Diccionario con scores de sentimiento
    """
    analyzer = SentimentAnalyzer(model_name) if model_name else SentimentAnalyzer()
    return analyzer.analyze_sentiment(text)


if __name__ == "__main__":
    # Test del analizador
    analyzer = SentimentAnalyzer()
    
    test_texts = [
        "I love this new product! It's amazing!",
        "This is terrible, worst experience ever.",
        "It's okay, nothing special but not bad either.",
        "Bitcoin is going to the moon! 🚀",
        "Crypto market is crashing, very worried 😰"
    ]
    
    print("Probando analizador de sentimientos:")
    print("=" * 50)
    
    for text in test_texts:
        result = analyzer.analyze_sentiment(text)
        print(f"Texto: {text}")
        print(f"Sentimiento: {result['predicted_sentiment']} (confianza: {result['confidence']:.3f})")
        print(f"Scores: {result}")
        print("-" * 30)