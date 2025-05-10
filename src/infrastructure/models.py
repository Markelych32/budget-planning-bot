from pydantic import BaseModel, Extra


class InternalModel(BaseModel):
    class Config:
        extra = Extra.forbid
        orm_mode = True
        use_enum_values = True
        allow_population_by_field_name = True
        validate_assignment = True
        arbitrary_types_allowed = True
        from_attributes = True


class FlexModel(BaseModel):
    class Config:
        extra = Extra.allow
        orm_mode = True
        use_enum_values = True
        allow_population_by_field_name = True
        validate_assignment = True
        arbitrary_types_allowed = True
        from_attributes = True
