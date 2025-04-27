from pydantic import BaseModel, EmailStr, field_validator


class UserRegistrationSchema(BaseModel):
    email: EmailStr
    username: str
    phone: str
    password: str
    password_confirm: str

    @field_validator('username')
    def validate_username(cls, username):
        if len(username) < 3:
            raise ValueError('Логин должен составлять хотя бы 3 символа.')
        if len(username) > 32:
            raise ValueError('Логин слишком длинный. Максимальная длина - 32.')
        return username
    
    @field_validator('phone')
    def validate_phone_number(cls, phone_number):
        if len(phone_number) < 12:
            raise ValueError('Номер телефона слишком короткий.')
        if len(phone_number) > 12:
            raise ValueError('Номер телефона слишком длинный.')
        return phone_number

    @field_validator('password')
    def validate_password(cls, password):
        if len(password) < 8:
            raise ValueError('Пароль слишком короткий. Минимальная длина пароля: 8.')
        return password

class UserLoginSchema(BaseModel):
    login: str
    password: str

class UpdatePhoneNumberSchema(BaseModel):
    phone: str
    
    @field_validator('phone')
    def validate_phone_number(cls, phone_number):
        if len(phone_number) < 12:
            raise ValueError('Номер телефона слишком короткий.')
        if len(phone_number) > 12:
            raise ValueError('Номер телефона слишком длинный.')
        return phone_number    