FROM python:3
RUN apt-get update -y && apt-get install -y build-essential
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
#RUN pip3 uninstall flask && python3 -m pip install flask
ENTRYPOINT ["python"]
CMD ["app.py"]