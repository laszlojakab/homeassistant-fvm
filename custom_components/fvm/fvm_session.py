# pylint: disable=bad-continuation
'''
Module for FVM session.
'''
import re
from datetime import datetime
from types import TracebackType
from typing import Any, Dict, Optional, Type

import aiohttp

ROOT_URL = 'https://ugyfelszolgalat.vizmuvek.hu'


class FvmCustomerServiceSession:
    '''
    VizmuvekCustomerServiceSession class represents
    a session at https://ugyfelszolgalat.vizmuvek.hu.
    '''

    def __init__(self):
        '''
        Initialize a new instance of VizmuvekCustomerServiceSession class.
        '''
        self._session = None

    async def __aenter__(self):
        self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType]
    ):
        await self._session.__aexit__(exc_type, exc_val, exc_tb)

    async def get_root_page(self) -> bytes:
        '''
        Loads the root page content.

        Returns
        -------
        bytes
            The root page content.
        '''
        async with self._session.get(ROOT_URL) as response:
            return await response.read()

    async def post_login(self, username: str, password: str) -> bool:
        '''
        Posts the login information.

        Parameters
        ----------
        username: str
            The username.
        password: str
            The password.

        Returns
        -------
        bool
            The value indicates whether the login was successful.
        '''
        async with self._session.get(
                f'{ROOT_URL}/Fiok/Bejelentkezes?ReturnUrl=/&_={self._get_timestamp()}',
                headers={
                    'X-Requested-With': 'XMLHttpRequest'
                }
        ) as response:
            response_text = await response.text()
            login_verification_token = re.search(
                '<input name="__RequestVerificationToken" type="hidden" value="(.*)" />',
                response_text,
                flags=re.MULTILINE
            ).group(1)

            resp = await self._session.post(
                f'{ROOT_URL}/Fiok/Bejelentkezes?ReturnUrl=%2F', data={
                    '__RequestVerificationToken': login_verification_token,
                    'LoginEmail': username,
                    'LoginPassword': password
                }, headers={
                    'X-Requested-With': 'XMLHttpRequest'
                })

            login_result = await resp.json()
            return login_result['Success'] and login_result['Object']['Success']

    async def get_locations_and_serial_numbers(self) -> Dict[str, Any]:
        '''
        Gets the locations and meter serial numbers.

        Returns
        -------
        Dict[str, Any]
            The locations and meter serial numbers.
        '''
        async with self._session.get(
            f'{ROOT_URL}/Meroallas/GetDiktLeolvIdoszakFogyHelyek?_={self._get_timestamp()}',
            headers={
                'X-Requested-With': 'XMLHttpRequest'
            }
        ) as params_request:
            return await params_request.json()

    async def get_dictation_and_reading_times(self, anlage: str, serge: str) -> Dict[str, Any]:
        '''
        Gets the dictation and reading times.

        Parameters
        ----------
        anlage: str
            The number of location.
        serge: str
            The meter serial number.

        Returns
        -------
        Dict[str, Any]
            The locations and meter serial numbers.
        '''
        async with self._session.get(
            f'{ROOT_URL}/Meroallas/LeolvasasiDiktalasiIdoszak?_={self._get_timestamp()}',
            headers={
                'X-Requested-With': 'XMLHttpRequest'
            }
        ) as response:
            text = await response.text()
            verification_token = re.search(
                '<input name="__RequestVerificationToken" type="hidden" value="(.*)" />',
                text,
                flags=re.MULTILINE
            ).group(1)

            async with self._session.post(
                    f'{ROOT_URL}/Meroallas/GetDiktalasiLeolvasasiIdoszakLisa',
                    headers={
                        'VerificationToken': verification_token,
                        'X-Requested-With': 'XMLHttpRequest',
                        'Accept': 'application/json, text/javascript, */*; q=0.01',
                        'Content-Type': 'application/json; charset=UTF-8',
                        'Cache-Control': 'no-cache',
                    },
                    data=f'{{"param": {{"I_ANLAGE": "{anlage}", "I_SERGE": "{serge}"}}}}'
            ) as reading_list_response:
                return await reading_list_response.json()

    def _get_timestamp(self):
        return round(datetime.now().timestamp() * 1000)
