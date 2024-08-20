FROM python:3.13-rc-alpine
LABEL authors="keaton"

RUN apk add --no-cache tzdata
ENV TZ=Asia/Shanghai

WORKDIR app
COPY requirements.txt .
# Install dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

# Run the application
CMD ["python3", "main.py"]