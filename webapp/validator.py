from aiohttp import web
import re

class IntegerValueError(Exception):
    """Thrown when integer value in wrong format"""


class IntegerRangeError(Exception):
    """Thrown when integer is outside permitted range"""


class PatternError(Exception):
    """Thrown when string doesn't adhere to patter"""


class NotABool(Exception):
    """Thrown when supplied value isn't a bool"""

class UnknownParameter(Exception):
    """Thrown when there is unknown parameter in request"""


def validate_integer(value, schema):

    try:
        intval = int(value)
        if "minimum" in schema and intval < schema["minimum"]:
            raise IntegerRangeError
        return intval
    except ValueError:
        raise IntegerValueError


def validate_string(value, schema):

    if (
        "pattern" in schema
        and re.match(string=value, pattern=schema["pattern"]) is None
    ):
        raise PatternError
    return value


def validate_bool(value, schema):
    if value not in ["true", "false"]:
        raise NotABool


def validate_param(value, schema):

    if schema["type"] == "integer":
        return validate_integer(value, schema)

    if schema["type"] == "string":
        return validate_string(value, schema)

    if schema["type"] == "bool":
        return validate_bool(value, schema)


def validate_method_params_against(parameters, schema):

    for param, value in parameters:

        if param not in schema:
            return web.json_response( status=400,
                data={"error": f"Parameter {param} is not recognized"}
            )

        try:
            validate_param(value, schema[param])
        except IntegerRangeError:
            return web.json_response(
                status=400,
                data={"error": f"Parameter {param} is outside of permitted range"},
            )
        except IntegerValueError:
            return web.json_response(
                status=400, data={"error": f"Parameter {param} is not a valid integer"}
            )
        except PatternError:

            return web.json_response(
                status=400, data={"error": f"Parameter {param} doesn't match pattern"}
            )
        except NotABool:
            return web.json_response(
                status=400, data={"error": f"Parameter {param} should be true or false"}
            )


@web.middleware
async def schema_validation(request, handler):

    if request.path not in request.app['schema']:
        return web.json_response(status=404, data={'error':'Not found'} )

    _parameters = request.app["schema"][request.path][request.method.lower()]["parameters"]

    parameters = {p["name"]: p for p in _parameters}

    response = validate_method_params_against(request.query.items(), parameters)
    if response is not None:
        return response
    return await handler(request)
