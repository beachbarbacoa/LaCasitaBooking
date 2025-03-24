import React, { useState } from 'react';
import { 
  View, 
  Text, 
  TextInput, 
  Button, 
  StyleSheet, 
  Alert,
  ScrollView,
  TouchableOpacity,
  FlatList
} from 'react-native';

const ReservationForm = () => {
  // State for form data
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    date: '',
    time: { hour: 7, minute: 0, ampm: 'PM' },
    diners: '1',
    seating: 'inside',
    pickup: 'no'
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const backendUrl = "https://your-render-url.onrender.com";

  // Time picker options
  const hours = Array.from({ length: 12 }, (_, i) => i + 1);
  const minutes = Array.from({ length: 60 }, (_, i) => i);
  const ampm = ['AM', 'PM'];

  // Handle form field changes
  const handleChange = (name, value) => {
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  // Handle time changes
  const handleTimeChange = (type, value) => {
    setFormData(prev => ({
      ...prev,
      time: { ...prev.time, [type]: value }
    }));
  };

  // Toggle AM/PM
  const toggleAMPM = () => {
    setFormData(prev => ({
      ...prev,
      time: { ...prev.time, ampm: prev.time.ampm === 'AM' ? 'PM' : 'AM' }
    }));
  };

  // Submit reservation
  const handleSubmit = async () => {
    setIsSubmitting(true);
    try {
      const reservation = {
        ...formData,
        time: `${formData.time.hour}:${String(formData.time.minute).padStart(2, '0')} ${formData.time.ampm}`
      };

      const response = await fetch(`${backendUrl}/reservations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(reservation)
      });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.message || 'Failed to submit reservation');
      }

      Alert.alert(
        "Success",
        data.message || "Reservation submitted successfully!",
        [{ text: "OK" }]
      );
    } catch (error) {
      Alert.alert(
        "Error",
        error.message || "An error occurred. Please try again.",
        [{ text: "OK" }]
      );
      console.error("Submission error:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.label}>Name:</Text>
      <TextInput
        style={styles.input}
        value={formData.name}
        onChangeText={(text) => handleChange('name', text)}
      />

      <Text style={styles.label}>Email:</Text>
      <TextInput
        style={styles.input}
        keyboardType="email-address"
        value={formData.email}
        onChangeText={(text) => handleChange('email', text)}
      />

      <Text style={styles.label}>Phone:</Text>
      <TextInput
        style={styles.input}
        keyboardType="phone-pad"
        value={formData.phone}
        onChangeText={(text) => handleChange('phone', text)}
      />

      <Text style={styles.label}>Date:</Text>
      <TextInput
        style={styles.input}
        placeholder="YYYY-MM-DD"
        value={formData.date}
        onChangeText={(text) => handleChange('date', text)}
      />

      <Text style={styles.label}>Time:</Text>
      <View style={styles.timePicker}>
        <FlatList
          horizontal
          data={hours}
          keyExtractor={(item) => item.toString()}
          renderItem={({ item }) => (
            <TouchableOpacity
              style={[
                styles.timeButton,
                formData.time.hour === item && styles.selectedTime
              ]}
              onPress={() => handleTimeChange('hour', item)}
            >
              <Text>{item}</Text>
            </TouchableOpacity>
          )}
        />
        
        <Text>:</Text>
        
        <FlatList
          horizontal
          data={minutes}
          keyExtractor={(item) => item.toString()}
          renderItem={({ item }) => (
            <TouchableOpacity
              style={[
                styles.timeButton,
                formData.time.minute === item && styles.selectedTime
              ]}
              onPress={() => handleTimeChange('minute', item)}
            >
              <Text>{String(item).padStart(2, '0')}</Text>
            </TouchableOpacity>
          )}
        />
        
        <FlatList
          horizontal
          data={ampm}
          keyExtractor={(item) => item}
          renderItem={({ item }) => (
            <TouchableOpacity
              style={[
                styles.timeButton,
                formData.time.ampm === item && styles.selectedTime
              ]}
              onPress={toggleAMPM}
            >
              <Text>{item}</Text>
            </TouchableOpacity>
          )}
        />
      </View>

      <Text style={styles.label}>Number of Diners:</Text>
      <FlatList
        horizontal
        data={Array.from({ length: 10 }, (_, i) => i + 1)}
        keyExtractor={(item) => item.toString()}
        renderItem={({ item }) => (
          <TouchableOpacity
            style={[
              styles.timeButton,
              formData.diners === item.toString() && styles.selectedTime
            ]}
            onPress={() => handleChange('diners', item.toString())}
          >
            <Text>{item}</Text>
          </TouchableOpacity>
        )}
      />

      <Text style={styles.label}>Seating Preference:</Text>
      <FlatList
        horizontal
        data={['Inside', 'Outside']}
        keyExtractor={(item) => item}
        renderItem={({ item }) => (
          <TouchableOpacity
            style={[
              styles.timeButton,
              formData.seating === item.toLowerCase() && styles.selectedTime
            ]}
            onPress={() => handleChange('seating', item.toLowerCase())}
          >
            <Text>{item}</Text>
          </TouchableOpacity>
        )}
      />

      <Text style={styles.label}>Require Pickup:</Text>
      <FlatList
        horizontal
        data={['No', 'Yes']}
        keyExtractor={(item) => item}
        renderItem={({ item }) => (
          <TouchableOpacity
            style={[
              styles.timeButton,
              formData.pickup === item.toLowerCase() && styles.selectedTime
            ]}
            onPress={() => handleChange('pickup', item.toLowerCase())}
          >
            <Text>{item}</Text>
          </TouchableOpacity>
        )}
      />

      <Button
        title={isSubmitting ? "Submitting..." : "Submit Reservation"}
        onPress={handleSubmit}
        disabled={isSubmitting}
      />
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    padding: 20,
  },
  input: {
    borderWidth: 1,
    borderColor: '#ccc',
    padding: 10,
    marginBottom: 15,
    borderRadius: 5,
  },
  label: {
    fontSize: 16,
    marginBottom: 5,
    marginTop: 10,
  },
  timePicker: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
  },
  timeButton: {
    padding: 10,
    margin: 5,
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 5,
  },
  selectedTime: {
    backgroundColor: '#ddd',
  },
});

export default ReservationForm;