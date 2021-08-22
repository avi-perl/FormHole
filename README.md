# Catch All Form Receiver (PostHole)

A restful API that allows for the rapid development of online forms by accepting nearly unstructured data, enabling
basic CRUD, and implementing basic security (eventually).

---

**Hosted:** https://post-hole.herokuapp.com/docs

**Repo:** https://github.com/avi-perl/PostHole

---

### TL;DR

There's are a million apps out there such as jotform where you can rapidly create forms, but I'm a developer and I want to
rapidly create feature full forms myself. This project is a light backend to do all the basic stuff so I can focus on
the form.

Also, I don't want to pay for jotform. Sorry 🤷🏻‍♂️

# Highlights

- Straightforward data schema to enable catch-all functionality

    ```jsx
    {
      model: "SomeModelName",        // Required field, specifies the type of data.
      version: 1.0,                  // Optional field, specifies version information about the data.
      data: {...},                   // Schema free data
      metadata: {...}                // Data about data, created datetime, delete status, etc. 
    }
    ```

- Ready for hosting on:

  - Heroku

## Missing Features

- No data models, if you need one you need your own app.
- Features. Seriously, if you need any special features just use Fast API or similar to whip up a quick custom app. This
  is a catch all receiver for rapid front end development.