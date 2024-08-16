FROM registry.access.redhat.com/ubi9/python-39@sha256:0176b477075984d5a502253f951d2502f0763c551275f9585ac515b9f241d73d

COPY ./src/pruner.py .

RUN pip install boto3
CMD python3 pruner.py