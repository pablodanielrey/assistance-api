####
# Primera etapa
####

FROM python:3.9

WORKDIR /src

RUN apt-get update && apt-get install -y \
  git \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

ENV TZ=America/Argentina/Buenos_Aires
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN pip install -U pip && pip install -U build

# solo hasta que libere el acceso al repo uso mi key
ENV GIT_SSH_COMMAND='ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i /src/id_rsa_github'
# ENV GIT_SSH_COMMAND='ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no'
# ADD ssh-private-key /src/id_rsa_github
RUN git clone https://github.com/pablodanielrey/assistance-api.git /src/assistance && echo "2022061301"

# genero los packages de las libs

RUN python -m build ./assistance


####
####   Segunda etapa
####
## ahora si el sistema para produccion

FROM python:3.9-slim-buster

# Prevents Python from writing pyc files to disc
ENV PYTHONDONTWRITEBYTECODE 1
# Prevents Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED 1

WORKDIR /src

COPY --from=0 /src/assistance/dist/assistance_api-2.0.1-py3-none-any.whl ./

# instalo el sistema.

RUN pip install -U pip
RUN pip install /src/assistance_api-2.0.1-py3-none-any.whl


CMD ["python3", "-m", "assistance.infra.cron"]
