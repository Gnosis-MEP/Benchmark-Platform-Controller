FROM henderake/dind:nvidia-docker
RUN curl https://bootstrap.pypa.io/get-pip.py | python3 && \
    pip install docker-compose
RUN curl -L https://packages.gitlab.com/install/repositories/runner/gitlab-runner/script.deb.sh | bash && \
    apt-get install -y gitlab-runner
WORKDIR /benchmark-platform-controller