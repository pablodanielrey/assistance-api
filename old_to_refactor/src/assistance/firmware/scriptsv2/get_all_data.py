import logging
import sys
from zk import ZK, const

import base64
from pydantic import BaseModel, validator


class User(BaseModel):
    uid: int
    name: str
    user_id: str
    password: str
    privilege: int
    card: str


class Fingerprint(BaseModel):
    uid: int
    fid: int
    size: int
    valid: int
    template: str

    @validator('template', pre=True)
    def template_conversion(cls, v:bytes):
        # raise ValueError('pompaaa')
        print(v)
        return base64.b64encode(v).decode('utf8')

    class Config:
        orm_mode = True


class CompleteUser(User):
    fingerprints: list[Fingerprint] = []

    class Config:
        orm_mode = True

class Data(BaseModel):
    users: list[CompleteUser] = []



def assign_to_user(fp: Fingerprint, users: list[CompleteUser]):
    for user in users:
        if user.uid == fp.uid:
            user.fingerprints.append(fp)
            return
    raise Exception(f'User {fp.uid} not found for fingerprint {fp.uid}')




if __name__ == '__main__':
    ip = sys.argv[1]
    data_file = sys.argv[2]
    print(ip)
    print(data_file)

    conn = None
    zk = ZK(ip, port=4370, timeout=5)
    print('Connecting to device ...')
    conn = zk.connect()
    try:
        
        data = Data()

        conn.enable_device()
        print('Firmware Version: : {}'.format(conn.get_firmware_version()))
        conn.test_voice()

        users = conn.get_users()
        for user in users:
            cuser = CompleteUser.from_orm(user)
            data.users.append(cuser)
            print(cuser.json())

        fps = conn.get_templates()
        for fp in fps:
            finger = Fingerprint.from_orm(fp)
            print(finger.json())
            assign_to_user(finger, data.users)    

        conn.enable_device()

        with open(data_file, 'w') as f:
            f.write(data.json())


    except Exception as e2:
        logging.exception(e2)
        conn.disconnect()
