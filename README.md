<p align="center">
  <img src="https://i.imgur.com/o5KFNIh.png" alt="Centered Image"/>
</p>
<h1 align="center" id="title">EVENTIVA</h1>
<br/>
<p id="description">Purchasing your favourite event with ease</p>
<ol>
  <li><a href="https://docs.google.com/document/d/1guzZgE9IGnuUP1E8EiU6zEAK6GQ3gVN0mYiIknzofn0/edit?usp=sharing">Project report & API documentation</a></li>
  <li><a href="https://www.canva.com/design/DAGgvwbA2D0/PEQJZt8Uccf0Y7b3NDOrGQ/edit">Project slides</a></li>
  <li>Project Demo video </li>
</ol>
<br/>

## Tech Stack

<!-- Services and UI -->
<h3>Services and UI</h3>
<p>
  <a href="https://flask.palletsprojects.com/"><img src="https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white" alt="Flask"/></a>
  <a href="https://vuejs.org/"><img src="https://img.shields.io/badge/Vue.js-35495E?style=for-the-badge&logo=vue.js&logoColor=4FC08D" alt="Vue.js"/></a>
  <a href="https://nodejs.org/en/docs"><img src="https://img.shields.io/badge/Node.js-339933?style=for-the-badge&logo=nodedotjs&logoColor=white" alt="Node.js"/></a>
  <a href="https://developer.mozilla.org/en-US/docs/Web/JavaScript"><img src="https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black" alt="JavaScript"/></a>
  <a href="https://www.outsystems.com/"><img src="https://img.shields.io/badge/Outsystems-E10A1D?style=for-the-badge&logo=outsystems&logoColor=white" alt="Outsystems"/></a>
</p>

<!-- API Gateway -->
<h3>API Gateway</h3>
<p>
  <a href="https://docs.konghq.com/"><img src="https://img.shields.io/badge/Kong-002659?style=for-the-badge&logo=kong&logoColor=white" alt="Kong API Gateway"/></a>
</p>

<!-- Database -->
<h3>Database</h3>
<p>
  <a href="https://www.mongodb.com/docs/"><img src="https://img.shields.io/badge/MongoDB-47A248?style=for-the-badge&logo=mongodb&logoColor=white" alt="MongoDB"/></a>
</p>

<!-- Message Broker -->
<h3>Message Broker</h3>
<p>
  <a href="https://www.rabbitmq.com/documentation.html"><img src="https://img.shields.io/badge/RabbitMQ-FF6600?style=for-the-badge&logo=rabbitmq&logoColor=white" alt="RabbitMQ"/></a>
</p>

<!-- Others -->
<h3>Others</h3>
<p>
  <a href="https://www.docker.com/"><img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker"/></a>
  <a href="https://developers.google.com/gmail/api"><img src="https://img.shields.io/badge/Gmail%20API-D14836?style=for-the-badge&logo=gmail&logoColor=white" alt="Gmail API"/></a>
  <a href="https://stripe.com/docs"><img src="https://img.shields.io/badge/Stripe-008CDD?style=for-the-badge&logo=stripe&logoColor=white" alt="Stripe"/></a>
</p>



<br/>

<h2>🛠️ Installation Steps:</h2>

<p>Copy or download files into a local directory, open a terminal and navigate to the path of the repo/files</p>

## Frontend

``` Javascript
1. cd frontend
2. Npm install
3. Npm run dev
```
## Backend
Make sure Docker desktop is running

### Pre-requisites:
``` Python
1. Set up exchanges, queues and routing keys on rabbitMQ (cd backend/atomic_service/notification_service)
2. Node amqp_setup.js
```

### To run backend:
``` Python
1. cd backend
2. python docker_build_all.py (To build all docker containers)
3. python docker_manage.py start (To start all docker containers)
4. python docker_manage.py stop (To stop all docker containers)
```

