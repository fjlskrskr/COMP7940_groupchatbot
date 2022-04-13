FROM python
COPY chatbot_main.py /
COPY requirements.txt /
RUN pip install pip update
RUN pip install -r requirements.txt
ENV ACCESS_TOKEN=5110206446:AAE6HFwDnfuw8DR04ScFadmfAmKHdVAz9rE
ENV HOST=comp7940chatbot.redis.cache.windows.net
ENV PASSWORD=Xk2zCLq4V7zk8Vhd78iwsuCeGOugjTsw8AzCaOWhQbY=
ENV REDISPORT=6380
CMD ["chatbot_main.py"]
ENTRYPOINT ["python"]