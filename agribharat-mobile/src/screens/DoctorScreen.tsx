import React, { useState } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  Image, ActivityIndicator, Alert, Dimensions
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import * as ImagePicker from 'expo-image-picker';
import { Camera, Upload, AlertTriangle, CheckCircle, ChevronLeft } from 'lucide-react-native';
import { useAppStore } from '../store/useAppStore';
import { api } from '../services/api';

const { width } = Dimensions.get('window');
const G = '#34c759';
const R = '#ff3b30';

export default function DoctorScreen({ navigation }: any) {
  const { selectedLanguage } = useAppStore();
  const hi = selectedLanguage === 'hi';

  const [imageUri, setImageUri] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState<any>(null);

  const requestPermission = async (): Promise<boolean> => {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert(
        hi ? 'अनुमति चाहिए' : 'Permission Required',
        hi ? 'फ़ोटो चुनने के लिए गैलरी की अनुमति दें।' : 'Please grant camera roll permissions to pick a photo.'
      );
      return false;
    }
    return true;
  };

  const pickImage = async (useCamera: boolean = false) => {
    if (!(await requestPermission())) return;

    let result;
    if (useCamera) {
      const { status } = await ImagePicker.requestCameraPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Permission Denied', 'Camera permission is required.');
        return;
      }
      result = await ImagePicker.launchCameraAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: true,
        aspect: [4, 3],
        quality: 0.8,
      });
    } else {
      result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: true,
        aspect: [4, 3],
        quality: 0.8,
      });
    }

    if (!result.canceled && result.assets && result.assets.length > 0) {
      setImageUri(result.assets[0].uri);
      setResult(null);
    }
  };

  const analyzeImage = async () => {
    if (!imageUri) return;
    setAnalyzing(true);
    
    try {
      const filename = imageUri.split('/').pop() || 'photo.jpg';
      const match = /\.(\w+)$/.exec(filename);
      const type = match ? `image/${match[1]}` : `image/jpeg`;

      const formData = new FormData();
      formData.append('file', { uri: imageUri, name: filename, type } as any);

      const result = await api.diagnosePlant(formData);
      
      setResult(result);
    } catch (error: any) {
      console.error(error);
      Alert.alert(
        hi ? 'विश्लेषण विफल' : 'Analysis Failed',
        hi ? 'फ़ोटो का विश्लेषण नहीं किया जा सका। कृपया पुनः प्रयास करें।' : 'Could not analyze photo. Please try again.'
      );
    } finally {
      setAnalyzing(false);
    }
  };

  const treatmentSteps = result?.treatment 
    ? result.treatment.split(/[.;]\s*/).filter((s: string) => s.trim().length > 0) 
    : [];

  return (
    <SafeAreaView style={st.container} edges={['top']}>
      <View style={st.header}>
        <TouchableOpacity style={st.backBtn} onPress={() => navigation.goBack()}>
          <ChevronLeft color="#fff" size={24} />
        </TouchableOpacity>
        <View style={st.headerTextContainer}>
          <Text style={st.brand}>{hi ? '🩺 KisaanAI डॉक्टर' : '🩺 Crop Doctor'}</Text>
          <Text style={st.tagline}>{hi ? 'पौधों की बीमारी पहचानें' : 'AI Plant Disease Detection'}</Text>
        </View>
        <View style={{ width: 40 }} />
      </View>

      <ScrollView contentContainerStyle={st.scroll} showsVerticalScrollIndicator={false}>
        {/* Upload Card */}
        <View style={st.uploadCard}>
          <LinearGradient colors={['rgba(245,158,11,0.08)', 'rgba(0,0,0,0)']} style={StyleSheet.absoluteFill} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} />
          {!imageUri ? (
            <View style={st.uploadPlaceholder}>
              <View style={st.uploadIconCircle}>
                <Upload color="#f59e0b" size={32} />
              </View>
              <Text style={st.uploadTitle}>{hi ? 'फ़ोटो अपलोड करें' : 'Upload a Photo'}</Text>
              <Text style={st.uploadHint}>
                {hi ? 'प्रभावित पत्ते या पौधे की साफ़ फ़ोटो अपलोड करें' : 'Upload a clear photo of the affected leaf or plant'}
              </Text>
              <View style={st.btnGroup}>
                <TouchableOpacity style={st.btnPrimary} onPress={() => pickImage(false)}>
                  <Upload color="#fff" size={18} />
                  <Text style={st.btnPrimaryText}>{hi ? 'गैलरी' : 'Gallery'}</Text>
                </TouchableOpacity>
                <TouchableOpacity style={st.btnSecondary} onPress={() => pickImage(true)}>
                  <Camera color="#fff" size={18} />
                  <Text style={st.btnSecondaryText}>{hi ? 'कैमरा' : 'Camera'}</Text>
                </TouchableOpacity>
              </View>
            </View>
          ) : (
            <View style={st.imagePreviewContainer}>
              <Image source={{ uri: imageUri }} style={st.imagePreview} />
              {!analyzing && !result && (
                <TouchableOpacity style={st.changeBtn} onPress={() => setImageUri(null)}>
                  <Text style={st.changeBtnText}>{hi ? 'बदलें' : 'Remove'}</Text>
                </TouchableOpacity>
              )}
            </View>
          )}
        </View>

        {/* Analyze Button */}
        {imageUri && !result && (
          <TouchableOpacity 
            style={[st.analyzeBtn, analyzing && st.analyzingBtn]} 
            onPress={analyzeImage} 
            disabled={analyzing}
            activeOpacity={0.8}
          >
            <LinearGradient colors={analyzing ? ['#1c1c1e', '#1c1c1e'] : ['#059669', '#10b981']} style={StyleSheet.absoluteFill} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} />
            {analyzing ? (
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 10 }}>
                <ActivityIndicator color="#fff" size="small" />
                <Text style={st.analyzeText}>{hi ? 'विश्लेषण हो रहा है...' : 'Analyzing...'}</Text>
              </View>
            ) : (
              <Text style={st.analyzeText}>{hi ? '🔬 स्कैन करें' : '🔬 Diagnose Disease'}</Text>
            )}
          </TouchableOpacity>
        )}

        {/* Reset Button */}
        {result && (
          <TouchableOpacity style={st.resetBtn} onPress={() => { setImageUri(null); setResult(null); }}>
            <Text style={st.resetBtnText}>{hi ? 'नई फ़ोटो स्कैन करें' : 'Scan Another Photo'}</Text>
          </TouchableOpacity>
        )}

        {/* Result Card */}
        {result && (
          <View style={st.resultCard}>
            <LinearGradient colors={['rgba(239,68,68,0.08)', 'rgba(0,0,0,0)']} style={StyleSheet.absoluteFill} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} />
            <View style={st.resultHeader}>
              <View style={st.alertIcon}>
                <AlertTriangle color={R} size={24} />
              </View>
              <View style={st.resultTitleWrap}>
                <Text style={st.resultLabel}>{hi ? 'बीमारी' : 'Diagnosis'}</Text>
                <Text style={st.diseaseName}>{result.disease_name}</Text>
              </View>
            </View>

            <View style={st.badgesRow}>
              <View style={st.badgeRed}>
                <Text style={st.badgeRedText}>
                  {hi ? 'गंभीरता' : 'Severity'}: {result.severity}
                </Text>
              </View>
              <View style={st.badgeGreen}>
                <Text style={st.badgeGreenText}>
                  {hi ? 'सटीकता' : 'Confidence'}: {(result.confidence * 100).toFixed(0)}%
                </Text>
              </View>
            </View>

            <View style={st.treatmentBox}>
              <View style={st.treatmentHeader}>
                <CheckCircle color={G} size={18} />
                <Text style={st.treatmentTitle}>{hi ? 'अनुशंसित उपचार' : 'Recommended Treatment'}</Text>
              </View>
              {treatmentSteps.length > 0 ? (
                treatmentSteps.map((step: string, idx: number) => (
                  <Text key={idx} style={st.treatmentStep}>• {step.trim()}</Text>
                ))
              ) : (
                <Text style={st.treatmentStep}>{result.treatment}</Text>
              )}
            </View>
          </View>
        )}
        <View style={{ height: 80 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

const st = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0a0a0a' },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 16, paddingVertical: 12, borderBottomWidth: 0.5, borderBottomColor: 'rgba(255,255,255,0.08)' },
  backBtn: { padding: 8, marginLeft: -8, width: 40 },
  headerTextContainer: { alignItems: 'center' },
  brand: { fontSize: 20, fontWeight: '800', color: '#fff' },
  tagline: { fontSize: 11, color: 'rgba(255,255,255,0.4)', marginTop: 2 },
  scroll: { padding: 20 },
  
  uploadCard: { borderRadius: 20, padding: 24, borderWidth: 1, borderStyle: 'dashed', borderColor: 'rgba(245,158,11,0.3)', overflow: 'hidden', minHeight: 280, justifyContent: 'center', alignItems: 'center' },
  uploadPlaceholder: { alignItems: 'center', width: '100%' },
  uploadIconCircle: { width: 72, height: 72, borderRadius: 36, backgroundColor: 'rgba(245,158,11,0.12)', justifyContent: 'center', alignItems: 'center', marginBottom: 16 },
  uploadTitle: { fontSize: 20, fontWeight: '700', color: '#fff', marginBottom: 6 },
  uploadHint: { color: 'rgba(255,255,255,0.4)', fontSize: 13, textAlign: 'center', marginBottom: 24, paddingHorizontal: 20, lineHeight: 18 },
  btnGroup: { flexDirection: 'row', gap: 12, width: '100%', maxWidth: 280 },
  btnPrimary: { flex: 1, backgroundColor: '#059669', paddingVertical: 14, borderRadius: 12, flexDirection: 'row', justifyContent: 'center', alignItems: 'center', gap: 8 },
  btnPrimaryText: { color: '#fff', fontSize: 15, fontWeight: '700' },
  btnSecondary: { flex: 1, backgroundColor: 'rgba(255,255,255,0.08)', paddingVertical: 14, borderRadius: 12, flexDirection: 'row', justifyContent: 'center', alignItems: 'center', gap: 8, borderWidth: 0.5, borderColor: 'rgba(255,255,255,0.1)' },
  btnSecondaryText: { color: '#fff', fontSize: 15, fontWeight: '600' },

  imagePreviewContainer: { width: '100%', height: 280, borderRadius: 16, overflow: 'hidden', position: 'relative' },
  imagePreview: { width: '100%', height: '100%', resizeMode: 'cover' },
  changeBtn: { position: 'absolute', top: 12, right: 12, backgroundColor: 'rgba(0,0,0,0.7)', paddingHorizontal: 16, paddingVertical: 8, borderRadius: 20, borderWidth: 0.5, borderColor: 'rgba(255,255,255,0.2)' },
  changeBtnText: { color: '#fff', fontSize: 12, fontWeight: '600' },

  analyzeBtn: { borderRadius: 16, alignItems: 'center', justifyContent: 'center', marginTop: 20, overflow: 'hidden', paddingVertical: 16 },
  analyzingBtn: {},
  analyzeText: { color: '#fff', fontSize: 17, fontWeight: '800' },

  resetBtn: { marginTop: 16, paddingVertical: 14, borderRadius: 12, borderWidth: 0.5, borderColor: 'rgba(255,255,255,0.15)', alignItems: 'center' },
  resetBtnText: { color: 'rgba(255,255,255,0.7)', fontSize: 14, fontWeight: '600' },

  resultCard: { borderRadius: 20, padding: 20, marginTop: 20, borderWidth: 0.5, borderColor: 'rgba(239,68,68,0.2)', overflow: 'hidden' },
  resultHeader: { flexDirection: 'row', alignItems: 'center', gap: 16, marginBottom: 16 },
  alertIcon: { width: 50, height: 50, borderRadius: 25, backgroundColor: 'rgba(255,59,48,0.12)', justifyContent: 'center', alignItems: 'center' },
  resultTitleWrap: { flex: 1 },
  resultLabel: { color: 'rgba(255,255,255,0.4)', fontSize: 11, textTransform: 'uppercase', letterSpacing: 1, marginBottom: 2 },
  diseaseName: { color: '#fff', fontSize: 20, fontWeight: '800' },
  
  badgesRow: { flexDirection: 'row', gap: 8, marginBottom: 20 },
  badgeRed: { backgroundColor: 'rgba(239,68,68,0.15)', paddingHorizontal: 12, paddingVertical: 6, borderRadius: 8 },
  badgeRedText: { color: '#f87171', fontSize: 12, fontWeight: '700' },
  badgeGreen: { backgroundColor: 'rgba(16,185,129,0.15)', paddingHorizontal: 12, paddingVertical: 6, borderRadius: 8 },
  badgeGreenText: { color: '#34d399', fontSize: 12, fontWeight: '700' },

  treatmentBox: { backgroundColor: 'rgba(255,255,255,0.04)', borderRadius: 14, padding: 16, borderWidth: 0.5, borderColor: 'rgba(255,255,255,0.06)' },
  treatmentHeader: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 12 },
  treatmentTitle: { color: '#fff', fontSize: 14, fontWeight: '700' },
  treatmentStep: { color: 'rgba(255,255,255,0.7)', fontSize: 14, lineHeight: 22, marginBottom: 6 },
});
