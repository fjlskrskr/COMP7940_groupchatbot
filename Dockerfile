FROM python
COPY app.py /
COPY requirements.txt /
EXPOSE 8000
RUN pip install pip update
RUN pip install -r requirements.txt
CMD ["app.py"]
ENTRYPOINT ["python"]