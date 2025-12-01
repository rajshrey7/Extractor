import os
import sys
import json
from typing import Dict, Any, List, Optional
from difflib import SequenceMatcher
import asyncio

# Import configuration (optional AI features)
# These are only needed for advanced AI-powered form filling
OPENROUTER_API_KEY = None
LLAMA_CLOUD_API_KEY = None
DEFAULT_MODEL = None
OPENROUTER_MODELS = {}

# Import JobFormFiller
try:
    from job_form_filler import JobFormFiller
except ImportError:
    JobFormFiller = None

class JobFormManager:
    def __init__(self):
        self.agent_path = os.path.dirname(__file__)
        self._ensure_agent_path()

    def _ensure_agent_path(self):
        """Ensure the agent path is in sys.path"""
        if os.path.exists(self.agent_path) and self.agent_path not in sys.path:
            sys.path.insert(0, self.agent_path)

    def _get_google_form_handler(self):
        """Lazy load GoogleFormHandler"""
        self._ensure_agent_path()
        try:
            from google_form_handler import GoogleFormHandler
            return GoogleFormHandler
        except ImportError:
            return None

    def analyze_form(self, form_url: str) -> Dict[str, Any]:
        """Analyze a Google Form and return its questions"""
        GoogleFormHandler = self._get_google_form_handler()
        if GoogleFormHandler is None:
            raise Exception("Google Form Handler module not available. Please ensure google_form_handler.py exists.")
        
        try:
            form_handler = GoogleFormHandler(url=form_url)
            questions_df = form_handler.get_form_questions_df(only_required=False)
            
            if questions_df.empty:
                raise Exception("Could not parse form. Make sure the form is publicly accessible.")
            
            return {
                "success": True,
                "form_url": form_url,
                "total_questions": len(questions_df),
                "questions": questions_df.to_dict(orient="records")
            }
        except Exception as e:
            raise Exception(f"Error analyzing form: {str(e)}")

    async def fill_form(self, form_url: str, extracted_data: Dict[str, Any], use_ai: bool = False) -> Dict[str, Any]:
        """Fill a job application form with OCR extracted data"""
        if use_ai:
            return await self._fill_form_with_ai_rag(form_url, extracted_data)
        else:
            if JobFormFiller is None:
                 raise Exception("JobFormFiller module not available.")
            
            try:
                filler = JobFormFiller()
                result = filler.fill_form_with_data(form_url, extracted_data)
                return result
            except Exception as e:
                raise Exception(f"Error filling form: {str(e)}")

    async def _fill_form_with_ai_rag(self, form_url: str, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Internal method for AI-powered filling (simulated RAG for now)"""
        # This mirrors the logic currently in app.py's fill_form_with_ai
        # Ideally this would use the full RAG workflow if available
        
        # Check for RAG dependencies
        try:
            from rag_workflow_with_human_feedback import RAGWorkflowWithHumanFeedback
            # If successful, we could use it, but the current app.py implementation 
            # for "use_ai=True" in /api/job-form/fill actually just falls back to 
            # JobFormFiller with a note, unless it's the specific /fill-ai endpoint.
            # I will preserve that behavior for consistency.
        except ImportError:
            pass

        if JobFormFiller is None:
             raise Exception("JobFormFiller module not available.")

        try:
            filler = JobFormFiller()
            result = filler.fill_form_with_data(form_url, extracted_data)
            
            if result.get("success"):
                result["ai_enhanced"] = False
                result["note"] = "Using intelligent field matching. For full AI-powered filling, upload a resume PDF."
            
            return result
        except Exception as e:
            # Fallback
            filler = JobFormFiller()
            return filler.fill_form_with_data(form_url, extracted_data)

    async def fill_form_ai_full(self, form_url: str, resume_index_path: str, model: str = None) -> Dict[str, Any]:
        """Fill job form using full AI-powered RAG workflow with resume index"""
        GoogleFormHandler = self._get_google_form_handler()
        if GoogleFormHandler is None:
            raise Exception("Google Form Handler module not available.")

        try:
            from rag_workflow_with_human_feedback import RAGWorkflowWithHumanFeedback
            from llama_index.core.workflow import StopEvent
        except ImportError:
             raise Exception("AI features are not installed. Please install 'llama-index' and related packages.")

        try:
            # Get form data
            form_handler = GoogleFormHandler(url=form_url)
            questions_df = form_handler.get_form_questions_df(only_required=False)
            form_data = questions_df.to_dict(orient="records")
            
            # Use default model if not specified
            selected_model = model or DEFAULT_MODEL
            if selected_model not in OPENROUTER_MODELS.values():
                selected_model = OPENROUTER_MODELS.get(selected_model, DEFAULT_MODEL)
            
            # Create workflow
            workflow = RAGWorkflowWithHumanFeedback(timeout=1000, verbose=True)
            
            # Run workflow
            handler = workflow.run(
                resume_index_path=resume_index_path,
                form_data=form_data,
                openrouter_key=OPENROUTER_API_KEY,
                llama_cloud_key=LLAMA_CLOUD_API_KEY,
                selected_model=selected_model
            )
            
            # Process events
            final_result = None
            async for event in handler.stream_events():
                if isinstance(event, StopEvent):
                    if hasattr(event, 'result') and event.result:
                        try:
                            if isinstance(event.result, str):
                                final_result = json.loads(event.result)
                            else:
                                final_result = event.result
                            break
                        except:
                            final_result = {"raw": str(event.result)}
            
            # Get final result if not received
            if not final_result:
                final_result = await handler
            
            return {
                "success": True,
                "form_data": final_result,
                "message": "Form filled using AI"
            }
            
        except Exception as e:
            raise Exception(f"Error in AI form filling: {str(e)}")

    def submit_form(self, form_url: str, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """Submit a filled job application form"""
        if JobFormFiller is None:
             raise Exception("JobFormFiller module not available.")
        
        try:
            filler = JobFormFiller()
            success = filler.submit_filled_form(form_url, form_data)
            
            return {
                "success": success,
                "message": "Form submitted successfully" if success else "Form submission failed",
                "form_url": form_url
            }
        except Exception as e:
            raise Exception(f"Error submitting form: {str(e)}")

    def get_filled_form_structure(self, form_url: str) -> Dict[str, Any]:
        """Get filled form data structure (for testing/debugging)"""
        GoogleFormHandler = self._get_google_form_handler()
        if GoogleFormHandler is None:
            raise Exception("Google Form Handler module not available.")
            
        try:
            form_handler = GoogleFormHandler(url=form_url)
            questions_df = form_handler.get_form_questions_df(only_required=False)
            
            return {
                "success": True,
                "form_url": form_url,
                "questions": questions_df.to_dict(orient="records"),
                "note": "This endpoint returns form structure. Use /api/job-form/fill to fill with data."
            }
        except Exception as e:
            raise Exception(f"Error getting form structure: {str(e)}")

    async def process_resume(self, file_content: bytes) -> Dict[str, Any]:
        """Process a resume PDF and create searchable index"""
        import tempfile
        
        # Check for resume processor dependencies
        try:
            from resume_processor import ResumeProcessor
        except ImportError as ie:
            error_msg = str(ie)
            if 'llama_parse' in error_msg.lower():
                return {
                    "success": False,
                    "error": "Resume processing requires llama-parse. Install with: pip install llama-parse llama-index",
                    "install_command": "pip install llama-parse llama-index"
                }
            else:
                return {
                    "success": False,
                    "error": f"Resume processor not available: {error_msg}"
                }
        
        # Save uploaded file temporarily
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(file_content)
                tmp_path = tmp_file.name
            
            # Process resume
            processor = ResumeProcessor(
                storage_dir="resume_indexes",
                llama_cloud_api_key=LLAMA_CLOUD_API_KEY
            )
            
            result = processor.process_file(tmp_path)
            
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            
            if result.get("success"):
                return {
                    "success": True,
                    "index_location": result["index_location"],
                    "num_nodes": result["num_nodes"],
                    "message": f"Resume processed successfully! Created {result['num_nodes']} searchable sections."
                }
            else:
                raise Exception(result.get("error", "Failed to process resume"))
                
        except Exception as e:
            # Ensure cleanup
            if 'tmp_path' in locals() and os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise Exception(f"Error processing resume: {str(e)}")
