from collections import namedtuple
from random import randint


class ENUM_CREATION_STATUS:
    REJECTED = -1
    OK = 0
    ALREADY_EXIST = 1


ConferenceCreationResult = namedtuple("ConferenceCreationResult", [
    'status',   # see ENUM_CREATION_STATUS
    'info',     # ConferenceInfo
    'message',  # message displayed to user if enum_creation_status == REJECTED
])


class ConferenceInfo(object):
    def __init__(self, room_name, conflict_id, mail_owner, start_time, duration):
        self.room_name = room_name
        self.conflict_id = conflict_id
        self.mail_owner = mail_owner
        self.start_time = start_time
        self.duration = duration

    def to_dict(self):
        # convert to payload expected by Jicofo
        return {
            'id': self.conflict_id,
            'name': self.room_name,
            'mail_owner': self.mail_owner,
            'start_time': self.start_time,
            'duration': self.duration,
        }


class ServiceBase(object):
    def create_conference(self, room_name, start_time, mail_owner):
        """ Make request to backend to verify conference creation.

        Args:
            room_name (str): Room name to create
            start_time (datetime.datetime): Meeting start time
            mail_owner (str): user identifier as provided by Jicofo

        Returns:
            ConferenceCreationResult
        """
        raise NotImplementedError

    def get_conference(self, conflict_id):
        """ Returns conference info given conflict id.

        Args:
            conflict_id (int): conflict id

        Returns:
            ConferenceInfo
        """
        raise NotImplementedError

    def delete_conference(self, conflict_id):
        """ Deletes conference if exists.

        Args:
            conflict_id (int): conflict id
        """
        return None


#  Store meeting data at module level so they persists across flask requests.
GLOBAL_MEETINGS = {}  # store meeting info indexed by conflict_id
GLOBAL_ID_MAPS = {}  # maps roomName to conflict_id
GLOBAL_USED_IDS = set()  # keeps track of used conflict_id so we can always generate a unique one


class DummyService(ServiceBase):
    DURATION = 6 * 3600  # Let meetings run for up to 6 hours

    def __init__(self):
        self.meetings = GLOBAL_MEETINGS
        self.id_map = GLOBAL_ID_MAPS
        self.used_ids = GLOBAL_USED_IDS

    def create_conference(self, room_name, start_time, mail_owner):
        conflict_id = self.id_map.get(room_name)
        if conflict_id:  # meeting already exist
            return ConferenceCreationResult(
                status=ENUM_CREATION_STATUS.ALREADY_EXIST,
                info=self.meetings[conflict_id],
                message=None,
            )

        # create new meeting
        info = self._create_and_store_conference(room_name=room_name, start_time=start_time, mail_owner=mail_owner)
        return ConferenceCreationResult(
            status=ENUM_CREATION_STATUS.OK,
            info=info,
            message=None,
        )

    def get_conference(self, conflict_id):
        return self.meetings.get(conflict_id, None)

    def delete_conference(self, conflict_id):
        self._delete_conference(conflict_id=conflict_id)

    def _create_and_store_conference(self, room_name, start_time, mail_owner):
        conflict_id = self._generate_conflict_id()
        info = ConferenceInfo(
            room_name=room_name,
            conflict_id=conflict_id,
            mail_owner=mail_owner,
            start_time=start_time,
            duration=self.DURATION,
        )
        self.meetings[conflict_id] = info
        self.id_map[room_name] = conflict_id

        return info

    def _delete_conference(self, conflict_id):
        info = self.meetings.pop(conflict_id, None)
        if info:
            self.id_map.pop(info.room_name)
        return info

    @staticmethod
    def _gen_9_digit_int():
        return randint(100000000, 999999999)

    def _generate_conflict_id(self):
        conflict_id = self._gen_9_digit_int()
        while conflict_id in self.used_ids:
            conflict_id = self._gen_9_digit_int()

        self.used_ids.add(conflict_id)
        return conflict_id
