from enum import Enum, IntEnum
from typing import Self


class BaseRank(Enum):
    def __new__(cls, level: int, title: str) -> Self:
        obj = object.__new__(cls)
        obj._value_ = (level, title)
        return obj

    @property
    def level(self) -> int:
        return self.value[0]

    @property
    def title(self) -> str:
        return self.value[1]


class BackendRank(BaseRank):
    INTERN = (1, "Backend Intern")
    JUNIOR = (2, "Junior Backend Developer")
    DEVELOPER = (3, "Backend Developer")
    SENIOR = (4, "Senior Backend Developer")
    STAFF = (5, "Staff Engineer")
    PRINCIPAL = (6, "Principal Engineer")
    DISTINGUISHED = (7, "Distinguished Engineer")
    FELLOW = (8, "Technical Fellow")
    VP = (9, "VP Engineering")
    CTO = (10, "CTO / Distinguished Engineer")


class FrontendRank(BaseRank):
    INTERN = (1, "Frontend Intern")
    JUNIOR = (2, "Junior Frontend Developer")
    DEVELOPER = (3, "Frontend Developer")
    SENIOR = (4, "Senior Frontend Developer")
    STAFF = (5, "Staff Frontend Engineer")
    PRINCIPAL = (6, "Principal Frontend")
    DISTINGUISHED = (7, "Distinguished UI Engineer")
    FELLOW = (8, "Technical Fellow (UI)")
    VP = (9, "VP Frontend Engineering")
    CTO = (10, "CTO / Lead UI Architect")


class DevOpsRank(BaseRank):
    INTERN = (1, "DevOps Intern")
    JUNIOR = (2, "Junior DevOps Engineer")
    PLATFORM = (3, "Platform Engineer")
    CLOUD_OPS = (4, "Cloud Operations")
    SRE = (5, "SRE Engineer")
    SENIOR_SRE = (6, "Senior SRE")
    PRINCIPAL_SRE = (7, "Principal SRE")
    DISTINGUISHED = (8, "Distinguished SRE")
    VP_PLATFORM = (9, "VP Platform Engineering")
    CTO_INFRA = (10, "CTO Infrastructure")


class QARank(BaseRank):
    INTERN = (1, "QA Intern")
    JUNIOR = (2, "Junior QA Engineer")
    ENGINEER = (3, "QA Engineer")
    SENIOR = (4, "Senior QA Engineer")
    STAFF = (5, "Staff Quality Engineer")
    PRINCIPAL = (6, "Principal QA Engineer")
    DISTINGUISHED = (7, "Distinguished QA")
    FELLOW = (8, "QA Fellow")
    VP_QUALITY = (9, "VP Quality Engineering")
    CHIEF_QA = (10, "Chief Quality Officer")


class ProductRank(BaseRank):
    INTERN = (1, "PM Intern")
    JUNIOR = (2, "Junior PM")
    OWNER = (3, "Product Owner")
    ASSOCIATE = (4, "Associate Product Manager")
    MANAGER = (5, "Product Manager")
    SENIOR_PM = (6, "Senior Product Manager")
    HEAD = (7, "Head of Product")
    VP_PRODUCT = (8, "VP Product")
    FELLOW = (9, "Product Fellow")
    CPO = (10, "Chief Product Officer")


class XPThreshold(IntEnum):
    LEVEL_1 = 0
    LEVEL_2 = 100
    LEVEL_3 = 300
    LEVEL_4 = 700
    LEVEL_5 = 1500
    LEVEL_6 = 2500
    LEVEL_7 = 4000
    LEVEL_8 = 6000
    LEVEL_9 = 8500
    LEVEL_10 = 10000
