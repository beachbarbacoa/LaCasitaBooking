import React, { useState, useEffect } from 'react';
import { View, Text, TextInput, Button, StyleSheet, Alert, ScrollView, TouchableOpacity, FlatList } from 'react-native';

const ReservationForm = () => {
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
  const [reservationIdInput, setReservationIdInput] = useState(''); // For manual testing in Expo Snack
  const backendUrl = "https://lacasitabooking.onrender.com";

  // Date picker logic
  const today = new Date();
  const [currentWeekStart, setCurrentWeekStart] = useState(new Date(today.setDate(today.getDate() - today.getDay())));

  const getWeekDates = (startDate) => {
    const dates = [];
    for (let i = 0; i < 7; i++) {
      const date = new Date(startDate);
      date.setDate(startDate.getDate() + i);
      dates.push(date);
    }
    return dates;
  };

  const handleDateChange = (newDate) => {
    setFormData(prev => ({ ...prev, date: newDate.toISOString().split('T')[0] }));
  };

  const handleWeekChange = (direction) => {
    const newStartDate = new Date(currentWeekStart);
    newStartDate.setDate(newStartDate.getDate() + (direction === 'next' ? 7 : -7));
    if (newStartDate >= new Date(new Date().setDate(new Date().getDate() - new Date().getDay()))) {
      setCurrentWeekStart(newStartDate);
    }
  };

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

  // Load reservation data from reservation_id
  const loadReservationData = (reservationId) => {
    if (reservationId) {
      fetch(`${backendUrl}/api/reservations/${reservationId}`)
        .then(response => {
          if (!response.ok) {
            throw new Error('Failed to fetch reservation');
          }
          return response.json();
        })
        .then(data => {
          const reservation = data.data;
          setFormData({
            name: reservation.name,
            email: reservation.email,
            phone: reservation.phone,
            date: reservation.date,
            time: parseTimeString(reservation.time),
            diners: reservation.diners.toString(),
            seating: reservation.seating,
            pickup: reservation.pickup
          });
        })
        .catch(error => {
          console.error("Error loading reservation:", error);
          Alert.alert("Error", "Could not load reservation details");
        });
    }
  };

  // Check for reservation_id in URL (web) or use manual input (Expo Snack)
  useEffect(() => {
    try {
      const params = new URLSearchParams(window.location.search);
      const reservationId = params.get('reservation_id');
      if (reservationId) {
        loadReservationData(reservationId);
      }
    } catch (e) {
      console.log("Not running in a browser environment or no query params");
    }
  }, []);

  // Helper function to parse time string
  const parseTimeString = (timeStr) => {
    const [timePart, ampm] = timeStr.split(' ');
    const [hour, minute] = timePart.split(':');
    return {
      hour: parseInt(hour),
      minute: parseInt(minute),
      ampm: ampm
    };
  };

  // Submit reservation with enhanced error handling
  const handleSubmit = async () => {
    setIsSubmitting(true);
    try {
      if (!formData.name || !formData.email || !formData.date) {
        throw new Error('Please fill in all required fields');
      }

      const reservation = {
        name: formData.name,
        email: formData.email,
        phone: formData.phone,
        date: formData.date,
        time: `${formData.time.hour}:${String(formData.time.minute).padStart(2, '0')} ${formData.time.ampm}`,
        diners: parseInt(formData.diners),
        seating: formData.seating,
        pickup: formData.pickup
      };

      const response = await fetch(`${backendUrl}/api/reservations`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify(reservation)
      });

      const responseData = await response.json();
      
      if (!response.ok) {
        throw new Error(responseData.message || `Server error: ${response.status}`);
      }

      Alert.alert(
        "Success", 
        "Reservation submitted successfully!",
        [{
          text: "OK",
          onPress: () => {
            setFormData({
              name: '',
              email: '',
              phone: '',
              date: '',
              time: { hour: 7, minute: 0, ampm: 'PM' },
              diners: '1',
              seating: 'inside',
              pickup: 'no'
            });
          }
        }]
      );
      
    } catch (error) {
      console.error("Submission error:", error);
      Alert.alert(
        "Error",
        error.message || "Failed to submit reservation",
        [{ text: "OK" }]
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      {/* Add a manual input for testing reservation_id in Expo Snack */}
      <Text style={styles.label}>Test Reservation ID (for Expo Snack):</Text>
      <TextInput
        style={styles.input}
        value={reservationIdInput}
        onChangeText={setReservationIdInput}
        placeholder="Enter reservation ID"
        keyboardType="numeric"
      />
      <Button
        title="Load Reservation Data"
        onPress={() => loadReservationData(reservationIdInput)}
      />

      <Text style={styles.label}>Name:</Text>
      <TextInput
        style={styles.input}
        value={formData.name}
        onChangeText={(text) => handleChange('name', text)}
        placeholder="Full Name"
      />

      <Text style={styles.label}>Email:</Text>
      <TextInput
        style={styles.input}
        keyboardType="email-address"
        value={formData.email}
        onChangeText={(text) => handleChange('email', text)}
        placeholder="email@example.com"
      />

      <Text style={styles.label}>Phone:</Text>
      <TextInput
        style={styles.input}
        keyboardType="phone-pad"
        value={formData.phone}
        onChangeText={(text) => handleChange('phone', text)}
        placeholder="Phone number"
      />

      <Text style={styles.label}>Date:</Text>
      <View style={styles.datePicker}>
        <View style={styles.weekDates}>
          {getWeekDates(currentWeekStart).map((dateObj, index) => (
            <View key={index} style={styles.dateContainer}>
              <TouchableOpacity
                onPress={() => handleDateChange(dateObj)}
                style={[
                  styles.dateButton, 
                  formData.date === dateObj.toISOString().split('T')[0] && styles.selectedDate
                ]}
              >
                <Text>{dateObj.toLocaleDateString('en-US', { weekday: 'short' })}</Text>
                <Text>{dateObj.toLocaleDateString('en-US', { day: 'numeric' })}</Text>
              </TouchableOpacity>
              {index === 0 && (
                <TouchableOpacity onPress={() => handleWeekChange('prev')} style={styles.arrowButton}>
                  <Text style={styles.arrow}>←</Text>
                </TouchableOpacity>
              )}
              {index === 6 && (
                <TouchableOpacity onPress={() => handleWeekChange('next')} style={styles.arrowButton}>
                  <Text style={styles.arrow}>→</Text>
                </TouchableOpacity>
              )}
            </View>
          ))}
        </View>
      </View>

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
    fontWeight: 'bold',
  },
  datePicker: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 20,
  },
  weekDates: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    flex: 1,
    marginHorizontal: 10,
  },
  dateContainer: {
    alignItems: 'center',
  },
  dateButton: {
    padding: 10,
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 5,
    alignItems: 'center',
    minWidth: 50,
  },
  selectedDate: {
    backgroundColor: '#e3f2fd',
    borderColor: '#2196f3',
  },
  arrowButton: {
    padding: 10,
    backgroundColor: '#f5f5f5',
    borderRadius: 5,
    marginTop: 10,
  },
  arrow: {
    fontSize: 24,
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
    minWidth: 40,
    alignItems: 'center',
  },
  selectedTime: {
    backgroundColor: '#e3f2fd',
    borderColor: '#2196f3',
  },
});

export default ReservationForm;