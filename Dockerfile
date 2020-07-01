FROM registry.insight-centre.org/sit/mps/docker-images/base-services:latest

RUN apt-get -q update && apt-get -qy install netcat && rm -rf /var/lib/apt/lists/*

RUN echo "Acquire::ForceIPv4 \"true\";"  > /etc/apt/apt.conf.d/99force-ipv4
RUN curl -4fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh && \
    pip install docker-compose && \
    rm -rf /tmp/pip* /root/.cache

ADD ./Pipfile /service/Pipfile
ADD ./setup.py /service/setup.py
RUN mkdir -p /service/benchmark_platform_controller/ && \
    touch /service/benchmark_platform_controller/__init__.py
WORKDIR /service
RUN rm -f Pipfile.lock && pipenv lock -vvv && pipenv --rm && \
    pipenv install --system  && \
    rm -rf /tmp/pip* /root/.cache

ADD . /service
RUN pip install -e . && \
    rm -rf /tmp/pip* /root/.cache


