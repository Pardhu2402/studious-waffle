import React, { useState, useEffect } from 'react';
import { WebView } from 'react-native-webview';
import { SafeAreaView, StatusBar, Text, View, ActivityIndicator, Button, Platform } from 'react-native';

export default function App() {
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [webViewKey, setWebViewKey] = useState(0);
  
  const serverUrl = Platform.select({
    web: 'http://172.16.15.222:5001/',
    default: 'http://172.16.15.222:5001/'
  });

  const reloadWebView = () => {
    setWebViewKey(prevKey => prevKey + 1);
    setHasError(false);
    setIsLoading(true);
  };

  const LoadingIndicatorView = () => (
    <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
      <ActivityIndicator size="large" color="#7C3AED" />
      <Text style={{ marginTop: 10, color: '#fff' }}>Loading...</Text>
    </View>
  );

  const ErrorView = () => (
    <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', padding: 20 }}>
      <Text style={{ color: 'red', marginBottom: 10 }}>Error loading content</Text>
      <Text style={{ textAlign: 'center', color: '#fff', marginBottom: 20 }}>{errorMessage}</Text>
      <Button title="Retry" onPress={reloadWebView} />
    </View>
  );

  if (Platform.OS === 'web') {
    window.location.href = serverUrl;
    return null;
  }

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: '#0F172A' }}>
      <StatusBar barStyle="light-content" />
      {hasError ? (
        <ErrorView />
      ) : (
        <WebView 
          key={webViewKey}
          source={{ uri: serverUrl }}
          style={{ flex: 1 }}
          allowsInlineMediaPlayback={true}
          mediaPlaybackRequiresUserAction={false}
          javaScriptEnabled={true}
          domStorageEnabled={true}
          originWhitelist={['*']}
          mixedContentMode="always"
          thirdPartyCookiesEnabled={true}
          renderLoading={LoadingIndicatorView}
          startInLoadingState={true}
          onLoadStart={(syntheticEvent) => {
            console.log('Loading started:', syntheticEvent.nativeEvent.url);
            setIsLoading(true);
          }}
          onLoadEnd={(syntheticEvent) => {
            console.log('Loading finished:', syntheticEvent.nativeEvent.url);
            setIsLoading(false);
          }}
          onError={(syntheticEvent) => {
            console.warn('WebView error:', syntheticEvent.nativeEvent);
            setHasError(true);
            setErrorMessage(`Failed to load: ${syntheticEvent.nativeEvent.description}`);
          }}
          onNavigationStateChange={(navState) => {
            console.log('Navigation State:', navState);
          }}
        />
      )}
      {isLoading && <LoadingIndicatorView />}
    </SafeAreaView>
  );
} 