class ExamplePlugin:
    def run(self, data):
        data["plugin_note"] = "Example plugin executed successfully."
        return data

def register():
    return ExamplePlugin()
