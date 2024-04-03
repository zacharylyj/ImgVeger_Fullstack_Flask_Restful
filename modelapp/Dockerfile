FROM tensorflow/serving
COPY / /
ENV MODEL_CONF=/model/models.config MODEL_BASE_PATH=/
EXPOSE 8500
EXPOSE 8501
RUN echo '#!/bin/bash \n\n\
    tensorflow_model_server \
    --rest_api_port=$PORT \
    --model_config_file=${MODEL_CONF} \
    "$@"' > /usr/bin/tf_serving_entrypoint.sh \
    && chmod +x /usr/bin/tf_serving_entrypoint.sh