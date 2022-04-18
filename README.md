Steps to prepare environment (checked on MacOS)
- 
- `mkdir venv3.8`
- `python3 -m venv venv3.8/`
- `. venv3.8/bin/activate`
- `pip3 install -r requirements.txt`

Steps to run test cases
-
- `locust -T <tag> -t <time to run> -u <number of users>`
- e.g. to execute test cases with tag `get` for 30 seconds with 10 users `locust -T get -t 30s -u 10`