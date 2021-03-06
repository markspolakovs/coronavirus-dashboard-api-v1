#!/usr/bin python3

"""
Constants
---------

Constants, which are used globally in the API service.

.. warning::
    Do not include secrets in this module. Use environment variables
    instead.

Author:        Pouria Hadjibagheri <pouria.hadjibagheri@phe.gov.uk>
Created:       23 May 2020
License:       MIT
Contributors:  Pouria Hadjibagheri
"""

# Imports
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Python:
from re import compile as re_compile, IGNORECASE
from os import getenv
from datetime import datetime
from typing import Set, Callable, Dict, Pattern, NamedTuple, Any, List
from string import Template

# 3rd party:

# Internal:
from .types import OrderingType, Transformer

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Header
__author__ = "Pouria Hadjibagheri"
__copyright__ = "Copyright (c) 2020, Public Health England"
__license__ = "MIT"
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

__all__ = [
    'MAX_QUERY_PARAMS',
    'DATE_PARAMS',
    'DEFAULT_STRUCTURE',
    'AUTHORISED_ORDERING_PARAMS',
    'DEFAULT_ORDERING',
    'DATA_TYPES',
    'TypePatterns',
    'DBQueries',
    'STRING_TRANSFORMATION',
    'MAX_DATE_QUERIES',
    'REPORT_DATE_PARAM_NAME',
    'RESPONSE_TYPE',
    'DATE_PARAM_NAME',
    "DatabaseCredentials",
    "RESTRICTED_PARAMETER_VALUES",
    "PAGINATION_PATTERN",
    "MAX_ITEMS_PER_RESPONSE",
    "DEFAULT_LATEST_ORDERING",
    "SELF_URL"
]


ENVIRONMENT = getenv("API_ENV", "PRODUCTION")

RESPONSE_TYPE = {
    "xml": "application/vnd.PHE-COVID19.v1+json; charset=utf-8",
    "json": "application/vnd.PHE-COVID19.v1+json; charset=utf-8",
    "csv": "text/csv; charset=utf-8"
}

MAX_ITEMS_PER_RESPONSE = 2500

REPORT_DATE_PARAM_NAME = 'releaseTimestamp'

MAX_DATE_QUERIES = 1

MAX_QUERY_PARAMS: int = 5

DATE_PARAM_NAME = "date"

DATE_PARAMS: Set[str] = {
    REPORT_DATE_PARAM_NAME,
    DATE_PARAM_NAME
}

DEFAULT_STRUCTURE: Dict[str, Any] = {
    "areaType": "areaType",
    "areaCode": "areaCode",
    "areaName": "areaName",
    "reportDate": REPORT_DATE_PARAM_NAME,
    "cases": {
        "specimenDate": "specimenDate",
        "dailyLabConfirmedCases": "dailyLabConfirmedCases",
        "previouslyReportedDailyCases": "previouslyReportedDailyCases",
        "changeInDailyCases": "changeInDailyCases",
        "totalLabConfirmedCases": "totalLabConfirmedCases",
        "previouslyReportedTotalCases": "previouslyReportedTotalCases",
        "changeInTotalCases": "changeInTotalCases",
        "dailyTotalLabConfirmedCasesRate": "dailyTotalLabConfirmedCasesRate",
        "casesRateInSevenDays": "casesRateInSevenDays",
    },
    "deaths": {
        "deathReportingDate": "deathReportingDate",
        "dailyChangeInDeaths": "dailyChangeInDeaths",
        "cumulativeDeaths": "cumulativeDeaths",
    }
}

AUTHORISED_ORDERING_PARAMS: Set[str] = {
    REPORT_DATE_PARAM_NAME,
    'date',
    'areaName',
    'areaCode',
    'areaType'
}


DEFAULT_ORDERING: OrderingType = [
    {"by": "releaseTimestamp", "ascending": False},
    {"by": "areaType", "ascending": True},
    {"by": "areaNameLower", "ascending": True},
    {"by": "date", "ascending": False},
]


DEFAULT_LATEST_ORDERING: OrderingType = [
    {"by": "releaseTimestamp", "ascending": False},
    {"by": "date", "ascending": False},
    {"by": "areaType", "ascending": True},
    {"by": "areaNameLower", "ascending": True}
]


PAGINATION_PATTERN: Pattern = re_compile(r'(page=(\d{,3}))')


class DatabaseCredentials(NamedTuple):
    host = getenv('AzureCosmosHost')
    key = getenv('AzureCosmosKey')
    db_name = getenv('AzureCosmosDBName')
    data_collection = getenv('AzureCosmosCollection')


if ENVIRONMENT == "DEVELOPMENT":
    SELF_URL = str()
elif ENVIRONMENT == "STAGING":
    SELF_URL = 'https://api.coronavirus-staging.data.gov.uk'
else:
    SELF_URL = 'https://api.coronavirus.data.gov.uk'


TypePatterns: Dict[Callable[[str], Any], Pattern] = {
    str: re_compile(r"[a-z]+", IGNORECASE),
    int: re_compile(r"\d{1,7}"),
    float: re_compile(r"[0-9.]{1,8}"),
    datetime: re_compile(r"\d{4}-\d{2}-\d{2}")
}

AREA_TYPES = {
    "utla": "utla",
    "ltla": "ltla",
    "region": "region",
    "nhsregion": "nhsRegion",
    "overview": "overview",
    "nation": "nation"
}

STRING_TRANSFORMATION = {
    'areaName': Transformer(
        value_fn=str.lower,
        param_fn=lambda n: n.replace("areaName", "areaNameLower")
    ),
    'areaType': Transformer(
        value_fn=lambda x: AREA_TYPES[str.lower(x)],
        param_fn=str
    ),
    'date': Transformer(
        value_fn=lambda x: x.split("T")[0],
        param_fn=str
    ),
    'areaCode': Transformer(value_fn=str.upper, param_fn=str),
    'DEFAULT': Transformer(value_fn=lambda x: x, param_fn=lambda x: x)
}


class DBQueries(NamedTuple):
    # noinspection SqlResolve,SqlNoDataSourceInspection
    data_query = Template("""\
SELECT  VALUE $template 
FROM    c 
WHERE   $clause_script 
$ordering
""".replace("\n", " "))

    # Query assumes that the data is ordered (descending) by date.
    # noinspection SqlResolve,SqlNoDataSourceInspection
    latest_date_for_metric = Template(f"""\
SELECT  TOP 1 (c.{ DATE_PARAM_NAME })
FROM    c
WHERE   $clause_script
        AND IS_DEFINED(c.$latest_by)
$ordering
""".replace("\n", " "))

    # noinspection SqlResolve,SqlNoDataSourceInspection
    exists = Template("""\
SELECT  TOP 1 VALUE (1)
FROM    c 
WHERE   $clause_script 
$ordering
    """.replace("\n", " "))

    count = Template("""\
SELECT  VALUE COUNT(1)
FROM    c 
WHERE   $clause_script 
$ordering
    """.replace("\n", " "))


DATA_TYPES: Dict[str, Callable[[str], Any]] = {
    'hash': str,
    'areaType': str,
    DATE_PARAM_NAME: datetime,
    'areaName': str,
    'areaNameLower': str,
    'areaCode': str,
    'covidOccupiedMVBeds': int,
    'cumAdmissions': int,
    'cumCasesByPublishDate': int,
    'cumPillarFourTestsByPublishDate': int,
    'cumPillarOneTestsByPublishDate': int,
    'cumPillarThreeTestsByPublishDate': int,
    'cumPillarTwoTestsByPublishDate': int,
    'cumTestsByPublishDate': int,
    'hospitalCases': int,
    'newAdmissions': int,
    'newCasesByPublishDate': int,
    'newPillarFourTestsByPublishDate': int,
    'newPillarOneTestsByPublishDate': int,
    'newPillarThreeTestsByPublishDate': int,
    'newPillarTwoTestsByPublishDate': int,
    'newTestsByPublishDate': int,
    'plannedCapacityByPublishDate': int,
    'newCasesBySpecimenDate': int,
    'cumCasesBySpecimenDate': int,
    'maleCases': list,
    'femaleCases': list,
    'cumAdmissionsByAge': list,

    "femaleDeaths28Days": int,
    "maleDeaths28Days": int,

    'changeInNewCasesBySpecimenDate': int,
    'previouslyReportedNewCasesBySpecimenDate': int,

    "cumCasesBySpecimenDateRate": float,
    'cumCasesByPublishDateRate': float,

    REPORT_DATE_PARAM_NAME: datetime,

    "newDeathsByDeathDate": int,
    "newDeathsByDeathDateRate": float,
    'newDeathsByDeathDateRollingRate': float,
    'newDeathsByDeathDateRollingSum': int,
    "cumDeathsByDeathDate": int,
    "cumDeathsByDeathDateRate": float,

    "newDeathsByPublishDate": int,
    "cumDeathsByPublishDate": int,
    "cumDeathsByPublishDateRate": float,

    "newDeaths28DaysByDeathDate": int,
    "newDeaths28DaysByDeathDateRate": float,
    'newDeaths28DaysByDeathDateRollingRate': float,
    'newDeaths28DaysByDeathDateRollingSum': int,
    "cumDeaths28DaysByDeathDate": int,
    "cumDeaths28DaysByDeathDateRate": float,

    "newDeaths28DaysByPublishDate": int,
    "cumDeaths28DaysByPublishDate": int,
    "cumDeaths28DaysByPublishDateRate": float,

    "newDeaths60DaysByDeathDate": int,
    "newDeaths60DaysByDeathDateRate": float,
    'newDeaths60DaysByDeathDateRollingRate': float,
    'newDeaths60DaysByDeathDateRollingSum': int,
    "cumDeaths60DaysByDeathDate": int,
    "cumDeaths60DaysByDeathDateRate": float,

    "newDeaths60DaysByPublishDate": int,
    "cumDeaths60DaysByPublishDate": int,
    "cumDeaths60DaysByPublishDateRate": float,

    'newOnsDeathsByRegistrationDate': int,
    'cumOnsDeathsByRegistrationDate': int,
    'cumOnsDeathsByRegistrationDateRate': float,

    "capacityPillarOneTwoFour": int,
    "newPillarOneTwoTestsByPublishDate": int,
    "capacityPillarOneTwo": int,
    "capacityPillarThree": int,
    "capacityPillarOne": int,
    "capacityPillarTwo": int,
    "capacityPillarFour": int,

    "cumPillarOneTwoTestsByPublishDate": int,

    "newPCRTestsByPublishDate": int,
    "cumPCRTestsByPublishDate": int,
    "plannedPCRCapacityByPublishDate": int,
    "plannedAntibodyCapacityByPublishDate": int,
    "newAntibodyTestsByPublishDate": int,
    "cumAntibodyTestsByPublishDate": int,

    "alertLevel": int,
    "transmissionRateMin": float,
    "transmissionRateMax": float,
    "transmissionRateGrowthRateMin": float,
    "transmissionRateGrowthRateMax": float,

    'newLFDTests': int,
    'cumLFDTests': int,
    'newVirusTests': int,
    'cumVirusTests': int,

    'newCasesBySpecimenDateDirection': str,
    'newCasesBySpecimenDateChange': int,
    'newCasesBySpecimenDateChangePercentage': float,
    'newCasesBySpecimenDateRollingSum': int,
    'newCasesBySpecimenDateRollingRate': float,
    'newCasesByPublishDateDirection': str,
    'newCasesByPublishDateChange': int,
    'newCasesByPublishDateChangePercentage': float,
    'newCasesByPublishDateRollingSum': int,
    'newCasesByPublishDateRollingRate': float,
    'newAdmissionsDirection': str,
    'newAdmissionsChange': int,
    'newAdmissionsChangePercentage': float,
    'newAdmissionsRollingSum': int,
    'newAdmissionsRollingRate': float,
    'newDeaths28DaysByPublishDateDirection': str,
    'newDeaths28DaysByPublishDateChange': int,
    'newDeaths28DaysByPublishDateChangePercentage': float,
    'newDeaths28DaysByPublishDateRollingSum': int,
    'newDeaths28DaysByPublishDateRollingRate': float,
    'newPCRTestsByPublishDateDirection': str,
    'newPCRTestsByPublishDateChange': int,
    'newPCRTestsByPublishDateChangePercentage': float,
    'newPCRTestsByPublishDateRollingSum': int,
    'newPCRTestsByPublishDateRollingRate': float,
    'newVirusTestsDirection': str,
    'newVirusTestsChange': int,
    'newVirusTestsChangePercentage': float,
    'newVirusTestsRollingSum': int,
    'newVirusTestsRollingRate': float,
}


# Values must be provided in lowercase characters.
# Example:
# { "areaName": ["united kingdom"] }
#
# The API will the refuse the respond to any queries
# whose filter value for a specific parameter is NOT
# in the list.
RESTRICTED_PARAMETER_VALUES: Dict[str, List[str]] = dict()

# if ENVIRONMENT != "DEVELOPMENT":
#     RESTRICTED_PARAMETER_VALUES.update({
#         "areaName": [
#             "united kingdom"
#         ],
#         "areaType": [
#             "overview",
#             "nation",
#             "nhsregion"
#         ]
#     })

if ENVIRONMENT == "DEVELOPMENT":
    DATA_TYPES: Dict[str, Callable[[str], Any]] = {
        'hash': str,
        'areaType': str,
        DATE_PARAM_NAME: datetime,
        'areaName': str,
        'areaNameLower': str,
        'areaCode': str,
        'changeInCumCasesBySpecimenDate': int,
        'changeInNewCasesBySpecimenDate': int,
        'cumPeopleTestedBySpecimenDate': int,
        'covidOccupiedMVBeds': int,
        'covidOccupiedNIVBeds': int,
        'covidOccupiedOSBeds': int,
        'covidOccupiedOtherBeds': int,
        'cumAdmissions': int,
        'cumAdmissionsByAge': list,
        'cumCasesByPublishDate': int,
        'cumCasesBySpecimenDate': int,
        # 'cumDeathsByDeathDate': int,
        # 'cumDeathsByPublishDate': int,
        'cumDischarges': int,
        'cumDischargesByAge': list,
        'cumNegativesBySpecimenDate': int,
        'cumPeopleTestedByPublishDate': int,
        # 'cumPillarFourPeopleTestedByPublishDate': int,  # Currently excluded.
        'cumPillarFourTestsByPublishDate': int,
        'cumPillarOnePeopleTestedByPublishDate': int,
        'cumPillarOneTestsByPublishDate': int,
        'cumPillarThreeTestsByPublishDate': int,
        'cumPillarTwoPeopleTestedByPublishDate': int,
        'cumPillarTwoTestsByPublishDate': int,
        'cumTestsByPublishDate': int,
        'femaleCases': list,
        # 'femaleDeaths': list,
        'femaleNegatives': list,
        'hospitalCases': int,
        'maleCases': list,
        # 'maleDeaths': list,
        'maleNegatives': list,
        'malePeopleTested': list,
        'femalePeopleTested': list,
        'newAdmissions': int,
        'newAdmissionsByAge': list,
        'newCasesByPublishDate': int,
        'newCasesBySpecimenDate': int,
        'newDischarges': int,
        'newNegativesBySpecimenDate': int,
        'newPeopleTestedByPublishDate': int,
        # 'newPillarFourPeopleTestedByPublishDate': int,   # Currently excluded.
        'newPillarFourTestsByPublishDate': int,
        'newPillarOnePeopleTestedByPublishDate': int,
        'newPillarOneTestsByPublishDate': int,
        'newPillarThreeTestsByPublishDate': int,
        'newPillarTwoPeopleTestedByPublishDate': int,
        'newPillarTwoTestsByPublishDate': int,
        'newTestsByPublishDate': int,
        'nonCovidOccupiedMVBeds': int,
        'nonCovidOccupiedNIVBeds': int,
        'nonCovidOccupiedOSBeds': int,
        'nonCovidOccupiedOtherBeds': int,
        'plannedCapacityByPublishDate': int,
        'plannedPillarFourCapacityByPublishDate': int,
        'plannedPillarOneCapacityByPublishDate': int,
        'plannedPillarThreeCapacityByPublishDate': int,
        'plannedPillarTwoCapacityByPublishDate': int,
        'previouslyReportedCumCasesBySpecimenDate': int,
        'previouslyReportedNewCasesBySpecimenDate': int,
        'suspectedCovidOccupiedMVBeds': int,
        'suspectedCovidOccupiedNIVBeds': int,
        'suspectedCovidOccupiedOSBeds': int,
        'suspectedCovidOccupiedOtherBeds': int,
        'totalBeds': int,
        'totalMVBeds': int,
        'totalNIVBeds': int,
        'totalOSBeds': int,
        'totalOtherBeds': int,
        'unoccupiedMVBeds': int,
        'unoccupiedNIVBeds': int,
        'unoccupiedOSBeds': int,
        'unoccupiedOtherBeds': int,
        REPORT_DATE_PARAM_NAME: datetime,
        'newPeopleTestedBySpecimenDate': int,

        "newDeathsByDeathDate": int,
        "newDeathsByDeathDateRate": float,
        'newDeathsByDeathDateRollingRate': float,
        "cumDeathsByDeathDate": int,
        "cumDeathsByDeathDateRate": float,

        "newDeathsByPublishDate": int,
        "cumDeathsByPublishDate": int,
        "cumDeathsByPublishDateRate": float,

        "newDeaths28DaysByDeathDate": int,
        "newDeaths28DaysByDeathDateRate": float,
        'newDeaths28DaysByDeathDateRollingRate': float,
        "cumDeaths28DaysByDeathDate": int,
        "cumDeaths28DaysByDeathDateRate": float,

        "newDeaths28DaysByPublishDate": int,
        "cumDeaths28DaysByPublishDate": int,
        "cumDeaths28DaysByPublishDateRate": float,

        "newDeaths60DaysByDeathDate": int,
        "newDeaths60DaysByDeathDateRate": float,
        'newDeaths60DaysByDeathDateRollingRate': float,
        "cumDeaths60DaysByDeathDate": int,
        "cumDeaths60DaysByDeathDateRate": float,

        "femaleDeaths28Days": int,
        "femaleDeaths60Days": int,
        "maleDeaths28Days": int,
        "maleDeaths60Days": int,

        "newDeaths60DaysByPublishDate": int,
        "cumDeaths60DaysByPublishDate": int,
        "cumDeaths60DaysByPublishDateRate": float,

        'newOnsDeathsByRegistrationDate': int,
        'cumOnsDeathsByRegistrationDate': int,
        'cumOnsDeathsByRegistrationDateRate': float,

        "cumCasesBySpecimenDateRate": float,
        "cumCasesByPublishDateRate": float,
        "cumPeopleTestedByPublishDateRate": float,
        "cumAdmissionsRate": float,
        "cumDischargesRate": float,

        "capacityPillarOneTwoFour": int,
        "newPillarOneTwoTestsByPublishDate": int,
        "capacityPillarOneTwo": int,
        "capacityPillarThree": int,
        "capacityPillarOne": int,
        "capacityPillarTwo": int,
        "capacityPillarFour": int,

        "newPillarOneTwoFourTestsByPublishDate": int,
        "newCasesBySpecimenDateRate": float,

        "cumPillarOneTwoTestsByPublishDate": int,

        "newPCRTestsByPublishDate": int,
        "cumPCRTestsByPublishDate": int,
        "plannedPCRCapacityByPublishDate": int,
        "plannedAntibodyCapacityByPublishDate": int,
        "newAntibodyTestsByPublishDate": int,
        "cumAntibodyTestsByPublishDate": int,

        "newDeathsByDeathDateRollingSum": int,
        "newDeaths28DaysByDeathDateRollingSum": int,
        "newDeaths60DaysByDeathDateRollingSum": int,

        'newLFDTests': int,
        'cumLFDTests': int,
        'newVirusTests': int,
        'cumVirusTests': int,

        "alertLevel": int,
        "transmissionRateMin": float,
        "transmissionRateMax": float,
        "transmissionRateGrowthRateMin": float,
        "transmissionRateGrowthRateMax": float,

        'newCasesBySpecimenDateDirection': str,
        'newCasesBySpecimenDateChange': int,
        'newCasesBySpecimenDateChangePercentage': float,
        'newCasesBySpecimenDateRollingSum': int,
        'newCasesBySpecimenDateRollingRate': float,
        'newCasesByPublishDateDirection': str,
        'newCasesByPublishDateChange': int,
        'newCasesByPublishDateChangePercentage': float,
        'newCasesByPublishDateRollingSum': int,
        'newCasesByPublishDateRollingRate': float,
        'newAdmissionsDirection': str,
        'newAdmissionsChange': int,
        'newAdmissionsChangePercentage': float,
        'newAdmissionsRollingSum': int,
        'newAdmissionsRollingRate': float,
        'newDeaths28DaysByPublishDateDirection': str,
        'newDeaths28DaysByPublishDateChange': int,
        'newDeaths28DaysByPublishDateChangePercentage': float,
        'newDeaths28DaysByPublishDateRollingSum': int,
        'newDeaths28DaysByPublishDateRollingRate': float,
        'newPCRTestsByPublishDateDirection': str,
        'newPCRTestsByPublishDateChange': int,
        'newPCRTestsByPublishDateChangePercentage': float,
        'newPCRTestsByPublishDateRollingSum': int,
        'newPCRTestsByPublishDateRollingRate': float,
        'newVirusTestsDirection': str,
        'newVirusTestsChange': int,
        'newVirusTestsChangePercentage': float,
        'newVirusTestsRollingSum': int,
        'newVirusTestsRollingRate': float,

        'newCasesBySpecimenDateDemographics': list,
        'newCasesByPublishDateDemographics': list,

        "newOnsCareHomeDeathsByRegistrationDate": int,
        "cumOnsCareHomeDeathsByRegistrationDate": int
    }
