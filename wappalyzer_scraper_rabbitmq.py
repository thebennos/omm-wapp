# Imports
import pika
from pika.exceptions import ConnectionClosed
from wappalyzer import Wappalyzer, WebPage
from threading import Thread
import time
import json
import sys

# Basic settings
AMQP_HOST = "85.25.103.85"
AMQP_PORT = 5672
AMQP_USER = "domains"
AMQP_PASS = "isdn300"
AMQP_RECEIVE_QUEUE = "domains_inbox_wappalyzer"
AMQP_SEND_QUEUE = "domains_outbox_wappalyzer"

# Run wappalyzer
def run_wappalyzer(domain):
    try:
        wappalyzer = Wappalyzer.latest()
        webpage = WebPage.new_from_url("http://{}".format(domain))
        data = wappalyzer.analyze(webpage)
        return data

    except Exception as e:
        print("Warning: Wappalyzer error {}".format(e))
        return None

# Callback
def callback(ch, method, properties, body):
    msg = json.loads(body.decode())
    id = msg["id"]
    domain = msg["domain"]
    print("Received {}".format(domain))
    data = run_wappalyzer(domain)
    if data:
        data = json.dumps({"id": id, "wappalyzer_json": list(data), "checked": time.time()})
        rmq_send(data)
    ch.basic_ack(delivery_tag = method.delivery_tag)

# RabbitMQ receive
def rmq_receive():
    try:
        credentials = pika.PlainCredentials(AMQP_USER, AMQP_PASS)
        parameters = pika.ConnectionParameters(AMQP_HOST, AMQP_PORT, "/", credentials)
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        channel.queue_declare(queue=AMQP_RECEIVE_QUEUE, durable=True)
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(callback, queue=AMQP_RECEIVE_QUEUE)
        channel.start_consuming()

    except ConnectionClosed:
        print("Warning: Connection closed, reconnecting...")
        rmq_receive()

# RabbitMQ send
def rmq_send(data):
    credentials = pika.PlainCredentials(AMQP_USER, AMQP_PASS)
    parameters = pika.ConnectionParameters(AMQP_HOST, AMQP_PORT, "/", credentials)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.queue_declare(queue=AMQP_SEND_QUEUE, durable=True)
    channel.basic_publish(exchange="", routing_key=AMQP_SEND_QUEUE, body=data)
    connection.close()

if __name__ == "__main__":
    try:
        if sys.argv[1] == "-t":
            threads = int(sys.argv[2])

            for i in range(threads):
                 t = Thread(target=rmq_receive)
                 t.start()

        else:
            print("Error: Unknown argument passed. Use -t to pass number of threads. [eg: -t 16]")
            input("Press enter to exit")
            sys.exit()

    except IndexError:
        print("Error: Argument -t is needed with a integer followed by. [eg: -t 16]")
        input("Press enter to exit")
        sys.exit()

    except ValueError:
        print("Error: Unexpected value passed in thread (-t) argument. Use integers.")
        input("Press enter to exit")
        sys.exit()
