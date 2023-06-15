
# Bitebyte - Cloud Computing Team



Cloud computing team responsible to build server infrastructure, create endpoint API for mobile , and create database for storing user information.


## Endpoint API

| Endpoint  | Method   | Description                              |
| :-------- | :------- | :-------------------------               |
| `/register` | `POST` | Users Register using username, email, password |
| `/login` | `POST` | Users can login using email and password |
| `/AddUsersIdentity` | `POST` | For Adding users age, gender, height, weight, etc. information |
| `/uploadImage` | `POST` | Users can change profiles photos |
| `/usersIdentity/"userId"` | `PUT` | Users can change their password |
| `/<int:age>/<int:gender>/<int:height>/<int:weight>/<int:healthconcern>/<int:menutype>/<int:activity>` | `GET` | Getting users Recipe from model |
| `/getAllFoodData` | `GET` | Getting all food data in Database |
| `/searchRecipeByName?name="foodName"` | `GET` | Getting name food that users search |



## Run Locally

Clone the project

```bash
  https://github.com/BiteByte-C23-PC678/Cloud-Computing.git
```

Go to the project directory

```bash
  cd Cloud-Computing
```

Install dependencies

```bash
  pip install -r requirements.txt
```

Start the server

```bash
  python main.py
```


## Deploy to Cloud Run
in this tutorial i am assuming you already have GCP account. if not you can make it.

1. Create your Google Cloud Platform project. 

2. clone this bitebyte project. 
```bash
git clone https://github.com/BiteByte-C23-PC678/Cloud-Computing.git
```
3. go to your cloud shell. in Google Cloud Platform you can click it in the right corner of your screen. it has terminal logo.

4. install cloud SDK  
``` 
gcloud init
```

5. Install the dependencies
```
pip install -r requirements.txt
```

6. build your image using the docker file
```
docker build submnit -t gcr.io/"ProjectID"/image-name
```

7. Deploy it to cloud run by using the latest container images.
```
gcloud run deploy SERVICE_NAME --image gcr.io/YOUR_PROJECT_ID/IMAGE_NAME --platform managed

```
8. after that Cloud run will give you URL or API. 

9. you can test all endpoint using postman