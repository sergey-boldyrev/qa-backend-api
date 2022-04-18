import datetime
import logging
from locust import TaskSet, User, between, events, runners, HttpUser, task, \
    tag, run_single_user
import json
from faker import Faker

curr_month = "2021-03"
time_format = "%Y-%m-%dT%H:%M:%S.000Z"
fake = Faker()
Faker.seed(0)


class APITaskSet(TaskSet):

    abstract = True
    endpoint = None

    def get(self):
        resp = self.client.get("/" + self.endpoint + "/")
        logging.debug(resp.text)
        assert resp.status_code == 200

    def create(self, post_json):
        resp_post = self.client.post("/" + self.endpoint + "/", json=post_json)
        logging.debug(resp_post.text)
        assert resp_post.status_code == 201
        try:
            resp_dict = resp_post.json()
        except ValueError:
            logging.error("parsing of response failed")
        # else:
            # assert name_string == resp_dict.get("name")
        new_id = resp_dict["id"]
        if new_id:
            APIUser.ids[self.endpoint].append(new_id)

        return new_id

    def get_id(self, id_to_check):
        resp_get_id = self.client.get("/" + self.endpoint + "/" + id_to_check)
        logging.debug(resp_get_id.text)
        assert resp_get_id.status_code == 200


class SlotsTaskSet(APITaskSet):

    slot_id = None
    endpoint = "slots"

    def on_start(self):
        self.slot_id = self.create_slot()
        # self.slot_id = "28c37b9d-71ae-4ec9-bdad-04cd956e2468"

    @tag('get')
    @task(1)
    def get_slots(self):
        super().get()

    @tag('get_id')
    @task(1)
    def get_slot_id(self):
        super().get_id(self.slot_id)

    @tag('create')
    @task(1)
    def create_slot(self):
        date_start = fake.date_time_this_month(before_now=False,
                                               after_now=True)
        date_end = date_start + datetime.timedelta(minutes=30)

        json_string = {"startAt": date_start.strftime(time_format),
                       "endAt": date_end.strftime(time_format)}
        new_id = super().create(json_string)
        return new_id


class UsersTaskSet(APITaskSet):

    user_id = None
    endpoint = "users"

    def on_start(self):
        self.user_id = self.create_user()

    @tag('get')
    @task(1)
    def get_users(self):
        super().get()

    @tag('get_id')
    @task(1)
    def get_users_id(self):
        super().get_id(self.user_id)

    @tag('create')
    @task(1)
    def create_user(self):
        name_string = fake.name()
        json_string = {"name": name_string}
        new_id = super().create(json_string)
        return new_id


class MeetingsTaskSet(APITaskSet):

    endpoint = "meetings"
    meeting_id = None

    def on_start(self):
        # self.meeting_id = self.create_meeting()
        pass

    @tag('get')
    @task(1)
    def get_meetings(self):
        super().get()

    @tag('get_id')
    @task(1)
    def get_meeting_id(self):
        super().get_id(self.meeting_id)

    @tag('create')
    @task(1)
    def create_meeting(self):
        user_id1 = UsersTaskSet.create_user(self, endpoint="users")
        user_id2 = UsersTaskSet.create_user(self, endpoint="users")
        slot_id = SlotsTaskSet.create_slot(self, endpoint="slots")
        json_string = {"slotId": slot_id, "title": "string",
                       "participants": [
                           {"id": user_id1},
                           {"id": user_id2}
                       ]
                       }

        new_id = super().create(json_string)
        return new_id


class CalendarsTaskSet(TaskSet):

    @task(1)
    def calendars(self):
        resp = self.client.get(f"/calendars?month={curr_month}")
        # logging.debug(resp.text)
        assert resp.status_code == 200


class APIUser(HttpUser):
    wait_time = between(5, 15)
    tasks = [UsersTaskSet, SlotsTaskSet, MeetingsTaskSet]
    ids = {"users": [], "slots": [], "meetings": []}

    def on_stop(self):
        # deleting all the explicitly created elements
        # TODO: add global flag to do this in one thread
        logging.debug(self.ids)
        for k in self.ids:
            logging.debug(k)
            if self.ids[k]:
                for id_to_remove in self.ids[k]:
                    resp_del = self.client.delete("/" + k + "/" + id_to_remove)
                    # assert resp_del.status_code == 200


# if launched directly, e.g. "python3 debug.py", not "locust -f debug.py"
if __name__ == "__main__":
    run_single_user(APIUser)
