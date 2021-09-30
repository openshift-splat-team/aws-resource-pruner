FROM registry.redhat.io/ubi8/python-38:1-71

COPY ./src/pruner.py .

RUN pip install boto3
CMD python3 pruner.py