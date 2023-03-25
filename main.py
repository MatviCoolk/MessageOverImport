import os

os.chdir("../MOIdata/")

from telethon import *
import multiprocess as mp
import asyncio

import time
import math
import json

# main
def main():
    print("\nMessageOverImport by \033[1m@MatviCoolk\033[0m\n"
          "This project\033[1m isn't created for any malicious purposes\033[0m\n")
    print(f"Time: {get_time()}\n\n")
    mp.Process(target=os.system, args=('echo "CAFFEINATE START"; caffeinate; echo "CAFFEINATE UNKNOWN END"', )).start()

    # it just works
    processes = []
    shared = SharedData()
    for i in range(5):
        processes.append(mp.Process(target=Client(shared, i).get_shared, args=(), name=f"MOI #{i}"))
        processes[i].start()
    for i in range(5):
        processes[i].join()

    shared.clients[0].client.run_until_disconnected()

# get time in my own timeline
def get_time():
    return round(time.time() // 60 - 27959040)

# it just works
def get_peer(chat_id):
    real_id, peer_type = utils.resolve_id(chat_id)
    return peer_type(real_id)

# read all files (config, login, data)
def read_all(config_file_name, login_file_name, data_file_name):
    data_file = open(data_file_name, "r")
    login_file = open(login_file_name, "r")
    config_file = open(config_file_name, "r")

    data = json.loads(data_file.read())
    login = json.loads(login_file.read())
    config = json.loads(config_file.read())

    data_file.close()
    login_file.close()
    config_file.close()

    return config, login, data

# shared data class with Clients
class SharedData:
    def __init__(self):
        self.config, self.login, self.data = read_all("config.json", "login.json", "data.json")

        self.receivers = []
        self.non_receivers = []
        self.clients = []

    def write_data(self):
        data_file = open("data.json", "w")
        data_file.write(json.dumps(self.data, indent=2))
        data_file.close()

# where the magic happens
class Client:
    def __init__(self, shared, num):
        self.anything_running = False
        try:
            loop = asyncio.get_event_loop()
        except:
            loop = asyncio.new_event_loop()

        self.shared_data = shared

        self.login = self.shared_data.login["clients"][num]
        self.num = num

        # receiver / non receiver
        self.receiver = self.login["receiver"]
        if self.receiver:
            self.shared_data.receivers.append(self)
        else:
            self.shared_data.non_receivers.append(self)
        self.shared_data.clients.append(self)

        # client stuff
        self.client = loop.run_until_complete(self.init_client())

        get_me = loop.run_until_complete(self.get_me())
        self.id, self.access_hash = get_me.id, get_me.access_hash
        self.input_user = types.InputPeerUser(self.id, self.access_hash)

        tag_events_to_client(self)
        self.uploaded_import_file = None

    def get_shared(self):
        return self.shared_data

    async def init_client(self):
        self.client = TelegramClient(self.login["session"], self.login["app_id"], self.login["app_hash"])
        await self.client.start(self.login["phone"], self.login["password"])
        await self.debug(f"Client initiated")
        return self.client

    async def async_init(self):
        await self.get_me()
        return

    async def debug(self, message, chat_id=0):
        message = f"{str(self.num).zfill(2)}: {message}"
        if chat_id == 0: chat_id = self.shared_data.config["undirected_log_id"]
        await self.client.send_message(chat_id, message)
        print(message)

    async def moi_disallowed_chat_check(self, event):
        ret = event.chat_id not in self.shared_data.config["moi_allowed_ids"]
        if ret: await self.client.send_message(event.chat_id, 'MOI commands are not allowed in this chat\n')
        return ret

    async def get_me(self):
        get_me = await self.client.get_me()
        self.id = get_me.id
        self.access_hash = get_me.access_hash
        self.input_user = types.InputPeerUser(self.id, self.access_hash)
        await self.debug(f"Get me")
        return get_me

    async def upload_import_file(self):
        self.uploaded_import_file = await self.client.upload_file(self.shared_data.config["import_file_name"])
        await self.debug(f"Import file uploaded")
        return self.uploaded_import_file

    async def id_command(self, event):
        real_id, peer_type = utils.resolve_id(event.chat_id)
        await self.client.send_message(event.chat_id,
                                       f"```Full chat ID: {event.chat_id}```\n"
                                       f"```════════════════════════════```\n"
                                       f"```{peer_type.__name__} : {real_id}```")

    async def create_group(self, event):
        if await self.moi_disallowed_chat_check(event): return

        group = await self.client(functions.messages.CreateChatRequest([client.id for client in self.shared_data.receivers], f'{self.num} : {str(len(self.shared_data.data["clients"][self.num]["groups"]["in_use"]["ids"]) % 1000).zfill(3)}'))
        chat_id = group.__dict__["chats"][0].__dict__["id"]
        group = await self.client(functions.messages.MigrateChatRequest(chat_id))
        chat_id = -group.__dict__["updates"][0].channel_id - 10 ** 12

        if self.num in [client.num for client in self.shared_data.non_receivers]:
            try:
                await self.client.edit_folder(chat_id, 1)
                await self.debug('Group moved into archive', event.chat_id)
            except Exception as ex:
                await self.debug(f'{ex}', event.chat_id)

        self.shared_data.data["clients"][self.num]["groups"]["in_use"]["ids"].append(chat_id)
        self.shared_data.data["clients"][self.num]["groups"]["in_use"]["counts"].append(0)
        self.shared_data.data["clients"][self.num]["groups"]["in_use"]["times"].append(0)
        self.shared_data.write_data()

        await self.debug('Data written', event.chat_id)

    async def check_import(self, event, import_chat_id):
        in_use = self.shared_data.data["clients"][self.num]["groups"]["in_use"]
        if import_chat_id not in in_use["ids"]:
            await self.debug("Group missing from data.json", event.chat_id)
            return "next", 0

        index = in_use["ids"].index(import_chat_id)

        if in_use["counts"][index] >= 4:
            await self.client.send_message('This group has already imported the maximum number of times', event.chat_id)
            await self.client.send_message('Group deleted', event.chat_id)
            self.shared_data.data["clients"][self.num]["groups"]["used_ids"].append(in_use["ids"][index])
            in_use["ids"].pop(index)
            in_use["times"].pop(index)
            in_use["counts"].pop(index)
            self.shared_data.write_data()
            await self.client.delete_dialog(get_peer(import_chat_id))
            return "next", index

        time_to_wait = min(in_use["times"]) - get_time() + 60 * 24

        if time_to_wait > 0:
            await self.debug(f'All groups have already been imported in the last day\n', event.chat_id)
            return "new", index

        time_to_wait = round(in_use["times"][index] + 60 * 24 - get_time())

        if in_use["times"][index] > get_time() - 60 * 24:
            await self.debug(f'This group has already been imported in the last day\n'
                             f'Wait {time_to_wait} minutes to import to this group again', event.chat_id)
            return "next", index

        time_to_wait = round(max(in_use["times"]) + 70 - get_time())

        if time_to_wait > 0:
            await self.debug(f'You have already imported in the last 70 minutes\n'
                             f'Wait {time_to_wait} minutes to import again', event.chat_id)
            return f"wait {time_to_wait}", index

        return "continue", index

    async def full_import(self, event, import_chat_id):
        self.anything_running = True

        result, index = await self.check_import(event, import_chat_id)
        if result != "continue":
            return result

        await self.debug("Import initiation", event.chat_id)
        try:
            init = await self.init_import(import_chat_id)

            await self.debug("Import initiated", event.chat_id)
            await self.debug("Import start", event.chat_id)
            try:
                await self.start_import(init, import_chat_id)
            except Exception as ex:
                await self.debug(str(ex), event.chat_id)
                return "start failed"
            await self.debug("Import started", event.chat_id)
            await self.client.send_message(import_chat_id, 'Import started')
        except Exception as ex:
            await self.debug(str(ex), event.chat_id)
            return "init failed"

        self.shared_data.data["clients"][self.num]["groups"]["in_use"]["counts"][index] += 1
        self.shared_data.data["clients"][self.num]["groups"]["in_use"]["times"][index] = get_time()
        self.shared_data.write_data()

        self.anything_running = False
        return "succeed"

    async def init_import(self, chat_id):
        return await self.client(functions.messages.InitHistoryImportRequest(
            peer=get_peer(chat_id),
            file=await self.upload_import_file(),
            media_count=0))

    async def start_import(self, init, chat_id):
        return await self.client(functions.messages.StartHistoryImportRequest(
            peer=get_peer(chat_id),
            import_id=init.id))

    async def start_command(self, event):
        if await self.moi_disallowed_chat_check(event): return

        if not self.anything_running:
            index = 0
            error_combo = 0
            next_combo = 0
            self.anything_running = True
            while self.anything_running:
                result = await self.full_import(event, self.shared_data.data["clients"][self.num]["groups"]["in_use"]["ids"][index])
                if result == "next":
                    next_combo += 1
                else:
                    if next_combo > 0:
                        await self.debug(f"next x{next_combo}", event.chat_id)
                    else:
                        await self.debug(result, event.chat_id)
                    next_combo = 0
                if result == "start failed":
                    await asyncio.sleep(10 * 60)
                if result == "succeed":
                    error_combo = 0
                    for i in range(20 * 20):
                        try:
                            await self.client.send_message(self.shared_data.data["clients"][self.num]["groups"]["in_use"]["ids"][index], f'Import {round(i / 4)}%')
                        except:
                            pass
                        await asyncio.sleep(3)
                elif result[0:4] == "wait":
                    await asyncio.sleep(int(result[5:]) * 60)
                    index -= 1
                elif result == "init failed" or result == "start failed":
                    await asyncio.sleep(1 * 60)
                    error_combo += 1

                elif result == "new":
                    done = False
                    while not done:
                        try:
                            await self.create_group(event)
                            await self.debug('Group created', event.chat_id)
                            done = True
                        except:
                            await asyncio.sleep(10 * 60)
                            await self.init_client()

                index = (index + 1) % len(self.shared_data.data["clients"][self.num]["groups"]["in_use"]["ids"])
                self.anything_running = True

def tag_events_to_client(self):
    @self.client.on(events.NewMessage(pattern='/id'))
    async def id_command_event_handler(event):
        await self.id_command(event)

    @self.client.on(events.NewMessage(pattern=f'/help'))
    async def help_command(event):
        await self.client.send_message(event.chat_id, "**Command list:**\n\n"
                                                      "/help - send a command list\n"
                                                      "/id - get current chat id\n\n"
                                                      "/import - import to this chat\n"
                                                      "/group - create import group")

    @self.client.on(events.NewMessage(pattern='/group', outgoing=True))
    async def create_group_command_event_handler(event):
        await self.create_group(event)

    @self.client.on(events.NewMessage(pattern='//group'))
    async def global_create_group_command_event_handler(event):
        await self.create_group(event)

    @self.client.on(events.NewMessage(pattern='/start', outgoing=True))
    async def local_start_command_event_handler(event):
        await self.start_command(event)

    @self.client.on(events.NewMessage(pattern='//start'))
    async def global_start_command_event_handler(event):
        await self.start_command(event)

    @self.client.on(events.NewMessage(pattern='/import', outgoing=True))
    async def import_command_event_handler(event):
        if not self.anything_running:
            await self.full_import(event, event.chat_id)

if __name__ == "__main__":
    main()