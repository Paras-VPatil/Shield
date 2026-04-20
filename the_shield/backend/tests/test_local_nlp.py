import pytest
from unittest.mock import MagicMock, patch

def test_local_model_loader_singleton():
    from app.services.local_model_loader import LocalModelLoader
    loader1 = LocalModelLoader()
    loader2 = LocalModelLoader()
    assert loader1 is loader2

@patch('app.services.local_model_loader.AutoModelForCausalLM.from_pretrained')
@patch('app.services.local_model_loader.AutoTokenizer.from_pretrained')
def test_local_model_loader_load(mock_tokenizer, mock_model):
    from app.services.local_model_loader import LocalModelLoader
    loader = LocalModelLoader()
    # Reset for test
    loader._model = None
    loader._tokenizer = None
    
    mock_model.return_value = MagicMock()
    mock_tokenizer.return_value = MagicMock()
    
    model, tokenizer = loader.load_model("mock-model") if hasattr(loader, 'load_model') else (MagicMock(), MagicMock())
    # Note: If use initialize() instead:
    loader.initialize()
    assert loader._model is not None

@patch('app.services.llm_service.get_local_model_loader')
def test_llm_service_local_summarize(mock_get_loader):
    from app.services.llm_service import LLMService
    mock_loader = MagicMock()
    mock_loader.generate.return_value = "This is a local summary."
    mock_get_loader.return_value = mock_loader
    
    # Force local mode for testing
    with patch.dict('os.environ', {'LLM_MODE': 'local'}):
        service = LLMService()
        summary = service.summarize("Test text", {}, "status", [], [], [])
        assert "local summary" in summary

@patch('app.services.llm_service.get_local_model_loader')
def test_llm_service_extract_capability_insights_json(mock_get_loader):
    from app.services.llm_service import LLMService
    mock_loader = MagicMock()
    
    mock_response = """
    {
        "complexity_score": 85,
        "decision_readiness_score": 70,
        "top_concepts": ["AI", "NLP"],
        "investigation_actions": ["Test"],
        "service_improvements": ["Scale"],
        "business_opportunities": ["New market"],
        "stakeholder_communications": ["Email"],
        "visualization_recommendations": ["Chart"]
    }
    """
    mock_loader.generate.return_value = mock_response
    mock_get_loader.return_value = mock_loader
    
    # We need to ensure mode is local
    with patch.dict('os.environ', {'LLM_MODE': 'local'}):
        service = LLMService()
        insights = service.extract_capability_insights("text")
        assert insights["complexity_score"] == 85
