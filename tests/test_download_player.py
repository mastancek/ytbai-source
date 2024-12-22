class TestDownloadAndPlayer:
    def test_download_progress(self, manager):
        """Test progress baru při stahování"""
        with patch('yt_dlp.YoutubeDL') as mock_ydl:
            mock_ydl.return_value.download.return_value = 0
            result = manager.process_download([sample_track])
            assert result is True

    def test_player_controls(self, manager):
        """Test ovládání přehrávače"""
        player = manager.player
        assert player.play("test.mp3") is True
        assert player.pause() is True
        assert player.stop() is True 

    def test_youtube_search(self, manager):
        """Test vyhledávání na YouTube"""
        query = "Metallica Master of Puppets"
        results = manager.search_music(query)
        
        assert len(results) > 0
        assert all(hasattr(r, 'video_id') for r in results)
        assert all(hasattr(r, 'title') for r in results)
        assert all(hasattr(r, 'artist') for r in results)
        assert all(hasattr(r, 'duration') for r in results)