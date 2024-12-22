class TestConfiguration:
    def test_load_config(self, manager):
        """Test načtení konfigurace"""
        config = manager._load_config()
        assert 'paths' in config
        assert 'ai_services' in config

    def test_save_config(self, manager):
        """Test uložení konfigurace"""
        manager.config['test_key'] = 'test_value'
        manager.save_config()
        
        # Ověření uložení
        loaded_config = manager._load_config()
        assert loaded_config['test_key'] == 'test_value'

    def test_first_run(self, manager):
        """Test prvního spuštění"""
        manager.config['first_run'] = True
        manager._first_run_wizard()
        assert not manager.config['first_run']
        assert Path(manager.config['paths']['music_dir']).exists() 