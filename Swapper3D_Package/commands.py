# Octoprint plugin name: Swapper3D, File: commands.py, Author: BigBrain3D, License: AGPLv3

from flask import request, jsonify
from .Swapper3D_utils import * #import all methods
from .Swap_utils import *
import time


def handle_command(self):
    data = request.json
    command = data.get("command")

    if command == "connect":
        if self.serial_conn is not None:
            self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message="Already connected."))
            return jsonify(result="False"), 500

        self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message="Received command: " + command))
        success, error = try_handshake(self)
        self.serial_conn = success #added manually

        if not success:
            self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"Handshake failed: {error}"))
            return jsonify(result="False", error=str(error)), 500

        if self.serial_conn is None:
            self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message="Connection lost after handshake."))
            return jsonify(result="False", error="Connection lost after handshake"), 500

        self._plugin_manager.send_plugin_message(self._identifier, dict(type="connectionState", message="Connected"))
        time.sleep(3)
        self._plugin_manager.send_plugin_message(self._identifier, dict(type="connectionState", message="Ready to Swap!"))
        return jsonify(result=str(success))

    elif command == "send":
        message = data.get("message")

        try:
            self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"Sending message: {message}"))
            self.serial_conn.write(message.encode())
            self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message="Message sent."))
        except Exception as e:
            self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"Failed to send message: {str(e)}"))
            return jsonify(result="False", error=str(e)), 500

        return jsonify(result="True")

    elif command == "disconnect":
        if self.serial_conn is not None:
            try:
                self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message="Disconnecting."))
                self.serial_conn.close()
                self.serial_conn = None
                self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message="Disconnected."))
                self._plugin_manager.send_plugin_message(self._identifier, dict(type="connectionState", message="Disconnected"))
            except Exception as e:
                self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"Failed to disconnect: {str(e)}"))
                return jsonify(result="False", error=str(e)), 500
        else:
            self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message="No connection to close."))
            return jsonify(result="False", error="No connection to close."), 500

        return jsonify(result="True")


    elif command == "swap to":
        insert_number = data.get("insert_number")

        # Debug log: Print the raw 'insert_number' value received
        self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"Raw insert_number received: {insert_number}"))

        try:
            insert_number = int(insert_number)
        # Ensure 'insert_number' is an integer
        except ValueError:
            # If 'insert_number' cannot be converted to an integer, log an error and return
            self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message="Invalid insert_number: cannot convert to integer"))
            return jsonify(result="False", error="Invalid insert_number: cannot convert to integer"), 400

        # Debug log: Print the validated 'insert_number' value
        self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"Validated insert_number: {insert_number}"))

        self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"Attempting to swap to insert#: {insert_number}"))

        try:
            success, error = swap_to_insert(self, insert_number)
            if not success:
                self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"Failed to swap to insert: {error}"))
                return jsonify(result="False", error=str(error)), 500
        except Exception as e:
            self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"Failed to swap to insert: {str(e)}"))
            return jsonify(result="False", error=str(e)), 500


        self._plugin_manager.send_plugin_message(self._identifier, dict(type="currentlyLoadedInsert", message=str(insert_number)))

        self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"Swapped to insert: {insert_number}"))
        return jsonify(result=str(success))
        
    elif command == "unload":
        self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message="Received command: " + command))
        try:
            success, error = unload_insert(self)
            if not success:
                self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"Unload failed: {error}"))
                return jsonify(result="False", error=str(error)), 500
        except Exception as e:
            self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"Exception during unload: {str(e)}"))
            return jsonify(result="False", error=str(e)), 500

        self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message="Unload successful"))
        return jsonify(result="True")
        
    elif command == "borealignon":
        self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message="Received command: " + command))
        try:
            positioned_for_bore_alignment(self)  # Call the positioning function instead of success and error check
            self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message="Bore alignment on successful"))
            self._plugin_manager.send_plugin_message(self._identifier, dict(type="connectionState", message="Bore alignment ON"))
            return jsonify(result="True")
        except Exception as e:
            self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"Exception during bore alignment on: {str(e)}"))
            return jsonify(result="False", error=str(e)), 500


    elif command == "borealignoff":
        self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message="Received command: " + command))
        try:
            success, error = bore_align_off(self)
            if not success:
                self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"Bore alignment off failed: {error}"))
                return jsonify(result="False", error=str(error)), 500
        except Exception as e:
            self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"Exception during bore alignment off: {str(e)}"))
            return jsonify(result="False", error=str(e)), 500

        self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message="Bore alignment off successful"))
        self._plugin_manager.send_plugin_message(self._identifier, dict(type="connectionState", message="Ready to Swap!"))
    
        return jsonify(result="True")

    else:
        self._plugin_manager.send_plugin_message(self._identifier, dict(type="log", message=f"Command not recognized: {command}"))
        return jsonify(result="False", error="Command not recognized."), 500
