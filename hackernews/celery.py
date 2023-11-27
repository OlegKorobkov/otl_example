import os
from celery import Celery
from celery.signals import worker_process_init
import time

from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.instrumentation.celery import CeleryInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
)

from opentelemetry import trace


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hackernews.settings')
tracer = trace.get_tracer("celery")


@worker_process_init.connect(weak=False)
def init_celery_tracing(*args, **kwargs):
    resource = Resource(attributes={
        SERVICE_NAME: "hackernews-old-celery"
    })

    processor = BatchSpanProcessor(OTLPSpanExporter(endpoint="http://localhost:4317"))
    console_processor = BatchSpanProcessor(ConsoleSpanExporter())

    provider = TracerProvider(resource=resource)
    provider.add_span_processor(processor)
    provider.add_span_processor(console_processor)

    trace.set_tracer_provider(provider)

    CeleryInstrumentor().instrument()


app = Celery('tasks', broker='amqp://localhost')
# app.config_from_object('django.conf:settings', namespace='CELERY')
# app.autodiscover_tasks()


@app.task
def add(x, y):
    res = x + y
    print(f'start add: {x} + {y}')
    trace.get_current_span().add_event(
        'add - start processing',
        {
            'x': x,
            'y': y
        }
    )
    time.sleep(2)
    with tracer.start_as_current_span("add - do job") as span:
        span.add_event('started')
        time.sleep(5)
        span.add_event('finished')

    time.sleep(1)
    with tracer.start_as_current_span("add - do more job") as span:
        time.sleep(3)
    print(f'finish add: {res}')
    trace.get_current_span().add_event(
        'add - end processing',
        {
            'result': res,
        }
    )
    return res
