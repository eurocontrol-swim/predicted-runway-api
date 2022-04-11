from app.models import TrainedModel
from app.config.file_dir import runway_models_dir
from app.models.runway.data_pipeline.data_pipeline import eham_input_pipeline, lfbo_input_pipeline,\
    lfpo_input_pipeline


TRAINED_MODELS_PER_AIRPORT = {
    "EHAM": TrainedModel(model_path=runway_models_dir.joinpath('EHAM.pkl'),
                         input_pipeline=eham_input_pipeline),
    "LFBO": TrainedModel(model_path=runway_models_dir.joinpath('LFBO.pkl'),
                         input_pipeline=lfbo_input_pipeline),
    "LFPO": TrainedModel(model_path=runway_models_dir.joinpath('LFPO.pkl'),
                         input_pipeline=lfpo_input_pipeline)
}

AIRPORTS = list(TRAINED_MODELS_PER_AIRPORT.keys())
