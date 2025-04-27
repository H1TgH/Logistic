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
        if len(phone_number) > 20:
            raise ValueError('Номер телефона слишком длинный.')
        return phone_number    
    
class UpdateNameSchema(BaseModel):
    name: str

    @field_validator('name')
    def validate_phone_number(cls, name):
        if len(name) < 2:
            raise ValueError('Имя слишком короткое.')
        if len(name) > 32:
            raise ValueError('Имя слишком длинное.')
        return name    
    
class UpdateSurnameSchema(BaseModel):
    surname: str

    @field_validator('surname')
    def validate_phone_number(cls, surname):
        if len(surname) < 2:
            raise ValueError('Фамилия слишком короткая.')
        if len(surname) > 32:
            raise ValueError('Фамилия слишком длинная.')
        return surname  