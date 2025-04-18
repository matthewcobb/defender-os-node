import { ref, onMounted, onBeforeUnmount } from 'vue';
import { AudioCommand, AudioData, WebMicrophone, decodeTypeMap } from 'node-carplay/web';
import { PcmPlayer } from 'pcm-ringbuf-player';
import { AudioPlayerKey, CarPlayWorker } from '../../../workers/types';
import { createAudioPlayerKey } from '../../../workers/utils';

const defaultAudioVolume = 1;
const defaultNavVolume = 0.5;

export function useCarplayAudio(worker: CarPlayWorker, microphonePort: MessagePort) {
  const mic = ref<WebMicrophone | null>(null);
  const audioPlayers = new Map<AudioPlayerKey, PcmPlayer>();

  const getAudioPlayer = (audio: AudioData): PcmPlayer => {
    const { decodeType, audioType } = audio;
    const format = decodeTypeMap[decodeType];
    const audioKey = createAudioPlayerKey(decodeType, audioType);
    let player = audioPlayers.get(audioKey);
    if (player) return player;
    player = new PcmPlayer(format.frequency, format.channel);
    audioPlayers.set(audioKey, player);
    player.volume(defaultAudioVolume);
    player.start();
    worker.postMessage({
      type: 'audioBuffer',
      payload: {
        sab: player.getRawBuffer(),
        decodeType,
        audioType,
      },
    });
    return player;
  };

  const processAudio = (audio: AudioData) => {
    if (audio.volumeDuration) {
      const { volume, volumeDuration } = audio;
      const player = getAudioPlayer(audio);
      player.volume(volume, volumeDuration);
    } else if (audio.command) {
      switch (audio.command) {
        case AudioCommand.AudioNaviStart:
          const navPlayer = getAudioPlayer(audio);
          navPlayer.volume(defaultNavVolume);
          break;
        case AudioCommand.AudioMediaStart:
        case AudioCommand.AudioOutputStart:
          const mediaPlayer = getAudioPlayer(audio);
          mediaPlayer.volume(defaultAudioVolume);
          break;
      }
    }
  };

  const initMic = async () => {
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: true,
      });
      const microphone = new WebMicrophone(mediaStream, microphonePort);
      mic.value = microphone;
    } catch (err) {
      console.error('Failed to init microphone', err);
    }
  };

  const startRecording = () => {
    mic.value?.start();
  };

  const stopRecording = () => {
    mic.value?.stop();
  };

  onMounted(() => {
    initMic();
  });

  onBeforeUnmount(() => {
    audioPlayers.forEach(p => p.stop());
  });

  return {
    processAudio,
    getAudioPlayer,
    startRecording,
    stopRecording
  };
}