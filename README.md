# Estimations API

[![CircleCI](https://circleci.com/gh/arnulfojr/scrum-estimations-api.svg?style=svg)](https://circleci.com/gh/arnulfojr/scrum-estimations-api)
[![CodeFactor](https://www.codefactor.io/repository/github/arnulfojr/scrum-estimations-api/badge)](https://www.codefactor.io/repository/github/arnulfojr/scrum-estimations-api)

Estimations API allows people to self host their scrum estimations service.
Allows full support for different values to use for estimating a task or ticket.

In order to be able to estimate a task there's some requirements:

- An organization is created
- All users must have an organization
- A session has to be created and is related to an organization
- A session can have multiple tasks to be estimated
- A user can then estimate tasks from the session

# Running tests

## Running locally

```bash
$ make run
```

## Running the linting

```bash
$ make lint
```

## Running API tests

```bash
$ make api-tests
```


# Contact

Arnulfo Solis
arnulfojr94@gmail.com
