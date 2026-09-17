class ConfigurationRepository:
    """
    ConfigurationRepository class to manage product configurations.
    """
    def __init__(self):
        self.configurations = []  # List to store product configurations

    def save_configuration(self, configuration):
        """
        Adds a product configuration to the repository.
        """
        self.configurations.append(configuration)