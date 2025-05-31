
# Step Definitions and Tooling

Steps can be `esoteric` and access the inside of the application,
or `exoteric` and access the application from outside, from REST.


## Caveats

### Usage of the generic `@step` def wrapper

We are using:

```python
from behave import step
```

We could use:

```python
from behave import given, when, then
```

But PyCharm 2020.1 won't understand the above.
It does understand `step`.

During the initial sprint, the IDE sugar was deemed more important.
Feel free to open an issue to discuss and|or re-evaluate this.


### I18N of error messages

Hamcrest has no I18N support whatsoever:
https://github.com/hamcrest/PyHamcrest/blob/632840d9ffe7fd4e9ea9ad6ac1db9ff3871cb984/src/hamcrest/core/assert_that.py#L65

