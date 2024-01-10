
# Define function directory

ARG FUNCTION_DIR="/app"

FROM public.ecr.aws/docker/library/python:3.11.7-slim as build-image


WORKDIR /tmp

RUN pip install poetry

COPY ./pyproject.toml ./poetry.lock* /tmp/

RUN poetry export --with test,boto3 -f requirements.txt --output requirements.txt --without-hashes

FROM public.ecr.aws/docker/library/python:3.11.7-slim

ARG FUNCTION_DIR
WORKDIR ${FUNCTION_DIR}

# Copy and install python dependencies
COPY --from=build-image /tmp/requirements.txt ${FUNCTION_DIR}/requirements.txt
RUN pip install --no-cache-dir --upgrade -r ${FUNCTION_DIR}/requirements.txt

# Copy function components code
COPY rooms_shared_services/src ${FUNCTION_DIR}/rooms_shared_services/src
COPY tests ${FUNCTION_DIR}/tests

COPY docker/main/entry_point.sh ${FUNCTION_DIR}/entry_point.sh

# Allow entry point file execution
RUN chmod 755 /app/entry_point.sh

ENTRYPOINT [ "/app/entry_point.sh" ]
