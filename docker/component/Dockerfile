
# Define function directory

ARG FUNCTION_DIR="/app"

FROM public.ecr.aws/docker/library/python:3.11.7-slim as build-image


WORKDIR /tmp

RUN pip install poetry

COPY ./pyproject.toml ./poetry.lock* /tmp/

RUN poetry export --with test -f requirements.txt --output requirements.txt --without-hashes

FROM public.ecr.aws/docker/library/python:3.11.7-slim

ARG FUNCTION_DIR
WORKDIR ${FUNCTION_DIR}

# Copy and install python dependencies
COPY --from=build-image /tmp/requirements.txt ${FUNCTION_DIR}/requirements.txt
RUN pip install --no-cache-dir --upgrade -r ${FUNCTION_DIR}/requirements.txt

# Copy code
COPY rooms_shared_services/src ${FUNCTION_DIR}/rooms_shared_services/src
COPY tests ${FUNCTION_DIR}/tests

CMD /usr/local/bin/python -m pytest ${FUNCTION_DIR}tests/component
