# Catch All Form Receiver

A restful API that allows for the rapid development of online forms by accepting unstructured data, enabling
basic CRUD, and implementing basic security (eventually).

[![Python application](https://github.com/avi-perl/PostHole/actions/workflows/python-app.yml/badge.svg)](https://github.com/avi-perl/PostHole/actions/workflows/python-app.yml)  [![CodeQL](https://github.com/avi-perl/PostHole/actions/workflows/codeql-analysis.yml/badge.svg)](https://github.com/avi-perl/PostHole/actions/workflows/codeql-analysis.yml)

---

**Hosted:** https://post-hole.herokuapp.com/docs

**Repo:** https://github.com/avi-perl/PostHole

---

## Uses

There's are many services where you can rapidly create web forms with good design and basic features. 
However, for advanced form features and design, these services are lacking. 
As a developer, I'd prefer to develop forms completely independently of a service

#### The quick and dirty way
1. 😊 Create a web form.
2. 😕 Build a back end API that accepts and handles data from the form.
3. 😡 Build (yet another) interface for managing records. (edit, delete, etc.)
4. 🤬 Deploy API into production.

#### With PostHole
1. 🥰 Create a web form, POST your form's data into a PostHole.

# Highlights

- Straightforward data schema to enable catch-all functionality

    ```jsx
    {
      model: "SomeModelName",        // Required field, specifies the type of data.
      version: 1.0,                  // Optional field, specifies version information about the data.
      data: {...},                   // Schema free data from your app.
  
      additional fields...           // PostHole manages fields like created datetime, delete status, etc. 
    }
    ```

- Ready for hosting:

  - Heroku
  - Local
  - AWS Lambda (coming soon...)

- Open API support.
- Swagger UI documentation.
- ReDoc documentation.

- Uses [SQLModel](https://sqlmodel.tiangolo.com/) / SQLAlchemy with support for:

  - SQLite
  - Postgresql
  - MySQL
  - Oracle
  - MS-SQL
  - Firebird
  - Sybase
  - and others

- Built with [FastAPI](https://fastapi.tiangolo.com/).

## Missing Features

- No data models. If you need one, you need your own app...
- Features. Seriously, if you need any special features just use Fast API or similar to whip up a quick custom app. This
  is a catch-all receiver for rapid front end development.

## Wish List
 - [ ] User accounts.
 - [ ] Email notifications on form submission.
 - [ ] History feature tracking changes to a record over time.
 - [ ] Stand-alone 100% static UI project for automatic viewing and editing of records.
 - [ ] Example application script using this project.
 - [ ] Scalability features
   - For example, if your dataset is public and may receive lots of traffic, if we cache the data somewhere like S3, 
   you could point a URL to this cached file (using AWS API Gateway as an example) and allow massive amounts of reading
   without the PostHole application getting used at all. This could make for an extremely scalable and free solution 
   when creating and editing records is infrequent. 
