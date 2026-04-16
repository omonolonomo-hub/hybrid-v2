import os
for f in ['test_floating_text.py', 'test_evolved_card.py', 'test_audio_system.py', 'run_shop_scene_demo.py']:
    p = f'c:\\Users\\Özhan\\Desktop\\hybrid\\{f}'
    if os.path.exists(p):
        os.remove(p)
        print(f'Deleted: {f}')
