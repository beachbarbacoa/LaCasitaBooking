import React, { useState, useEffect } from 'react';
import { View, Text, TextInput, Button, StyleSheet, ScrollView, TouchableOpacity, FlatList } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';

// Create a stack navigator
const Stack = createStackNavigator();

// Main Reservation Form Component
const ReservationForm = ({ navigation, route }) => {
  const reservationId = route.params?.reservationId;

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [date, setDate] = useState('');
  const [time, setTime] = useState({ hour: 7, minute: 0, ampm: 'AM' });
  const [diners, setDiners] = useState('1');
  const [seating, setSeating] = useState('inside');
  const [pickup, setPickup] = useState('no');
  const [reservationStatus, setReservationStatus] = useState('Pending'); // New state for reservation status

  const backendUrl = "https://lacasitabooking.onrender.com"; // Updated to your Render backend URL

  // Date Picker Logic
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
    setDate(newDate.toISOString().split('T')[0]); // Format as YYYY-MM-DD
  };

  const handleWeekChange = (direction) => {
    const newStartDate = new Date(currentWeekStart);
    newStartDate.setDate(newStartDate.getDate() + (direction === 'next' ? 7 : -7));
    if (newStartDate >= new Date(new Date().setDate(new Date().getDate() - new Date().getDay()))) {
      setCurrentWeekStart(newStartDate);
    }
  };

  // Time Picker Logic
  const handleTimeChange = (type, value) => {
    setTime((prev) => ({ ...prev, [type]: value }));
  };

  const toggleAMPM = () => {
    setTime((prev) => ({ ...prev, ampm: prev.ampm === 'AM' ? 'PM' : 'AM' }));
  };

  // Fetch reservation details if reservationId is present
  useEffect(() => {
    if (reservationId) {
      fetch(`${backendUrl}/reservations/${reservationId}`)
        .then((response) => response.json())
        .then((data) => {
          setName(data.name);
          setEmail(data.email);
          setPhone(data.phone);
          setDate(data.date);
          setTime(data.time);
          setDiners(data.diners);
          setSeating(data.seating);
          setPickup(data.pickup);
          setReservationStatus(data.status); // Update the reservation status
        });
    }
  }, [reservationId]);

  const handleSubmit = async () => {
    const reservation = {
      name,
      email,
      phone,
      date,
      time: `${time.hour}:${String(time.minute).padStart(2, '0')} ${time.ampm}`,
      diners,
      seating,
      pickup,
    };

    try {
      const response = await fetch(`${backendUrl}/reservations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(reservation),
      });

      if (!response.ok) {
        const errorData = await response.json();
        console.error("Backend error:", errorData);
        alert(`Failed to submit reservation: ${errorData.message}`);
        return;
      }

      const data = await response.json();
      alert(data.message);
    } catch (error) {
      console.error("Frontend error:", error);
      alert('Failed to submit reservation. Please try again later.');
    }
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text>Name:</Text>
      <TextInput value={name} onChangeText={setName} style={styles.input} />

      <Text>Email:</Text>
      <TextInput value={email} onChangeText={setEmail} style={styles.input} />

      <Text>Phone:</Text>
      <TextInput value={phone} onChangeText={setPhone} style={styles.input} />

      <Text>Date:</Text>
      <View style={styles.datePicker}>
        <View style={styles.weekDates}>
          {getWeekDates(currentWeekStart).map((dateObj, index) => (
            <View key={index} style={styles.dateContainer}>
              <TouchableOpacity
                onPress={() => handleDateChange(dateObj)}
                style={[styles.dateButton, date === dateObj.toISOString().split('T')[0] && styles.selectedDate]}
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

      <Text>Time:</Text>
      <View style={styles.timePicker}>
        <FlatList
          horizontal
          data={Array.from({ length: 12 }, (_, i) => ({ id: i + 1, label: `${i + 1}` }))}
          keyExtractor={(item) => item.id.toString()}
          renderItem={({ item }) => (
            <TouchableOpacity
              style={[styles.timeButton, time.hour === item.id && styles.selectedTime]}
              onPress={() => handleTimeChange('hour', item.id)}
            >
              <Text>{item.label}</Text>
            </TouchableOpacity>
          )}
        />
        <Text>:</Text>
        <FlatList
          horizontal
          data={Array.from({ length: 60 }, (_, i) => ({ id: i, label: i.toString().padStart(2, '0') }))}
          keyExtractor={(item) => item.id.toString()}
          renderItem={({ item }) => (
            <TouchableOpacity
              style={[styles.timeButton, time.minute === item.id && styles.selectedTime]}
              onPress={() => handleTimeChange('minute', item.id)}
            >
              <Text>{item.label}</Text>
            </TouchableOpacity>
          )}
        />
        <FlatList
          horizontal
          data={[{ id: 1, label: 'AM' }, { id: 2, label: 'PM' }]}
          keyExtractor={(item) => item.id.toString()}
          renderItem={({ item }) => (
            <TouchableOpacity
              style={[styles.timeButton, time.ampm === item.label && styles.selectedTime]}
              onPress={() => handleTimeChange('ampm', item.label)}
            >
              <Text>{item.label}</Text>
            </TouchableOpacity>
          )}
        />
      </View>

      <Text>Number of Diners:</Text>
      <FlatList
        horizontal
        data={Array.from({ length: 10 }, (_, i) => ({ id: i + 1, label: `${i + 1}` }))}
        keyExtractor={(item) => item.id.toString()}
        renderItem={({ item }) => (
          <TouchableOpacity
            style={[styles.timeButton, diners === item.label && styles.selectedTime]}
            onPress={() => setDiners(item.label)}
          >
            <Text>{item.label}</Text>
          </TouchableOpacity>
        )}
      />

      <Text>Seating Preference:</Text>
      <FlatList
        horizontal
        data={[{ id: 1, label: 'Inside' }, { id: 2, label: 'Outside' }]}
        keyExtractor={(item) => item.id.toString()}
        renderItem={({ item }) => (
          <TouchableOpacity
            style={[styles.timeButton, seating === item.label.toLowerCase() && styles.selectedTime]}
            onPress={() => setSeating(item.label.toLowerCase())}
          >
            <Text>{item.label}</Text>
          </TouchableOpacity>
        )}
      />

      <Text>Require Pickup and Drop-off?</Text>
      <FlatList
        horizontal
        data={[{ id: 1, label: 'No' }, { id: 2, label: 'Yes' }]}
        keyExtractor={(item) => item.id.toString()}
        renderItem={({ item }) => (
          <TouchableOpacity
            style={[styles.timeButton, pickup === item.label.toLowerCase() && styles.selectedTime]}
            onPress={() => setPickup(item.label.toLowerCase())}
          >
            <Text>{item.label}</Text>
          </TouchableOpacity>
        )}
      />

      <Text>Reservation Status: {reservationStatus}</Text> {/* Display reservation status */}

      <Button title="Submit Reservation" onPress={handleSubmit} />
    </ScrollView>
  );
};

// App Component with Navigation
const App = () => {
  return (
    <NavigationContainer>
      <Stack.Navigator>
        <Stack.Screen
          name="ReservationForm"
          component={ReservationForm}
          options={{ title: 'Make a Reservation' }}
        />
      </Stack.Navigator>
    </NavigationContainer>
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
    marginBottom: 10,
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
  },
  selectedDate: {
    backgroundColor: '#ddd',
  },
  arrowButton: {
    padding: 10,
    backgroundColor: '#f0f0f0',
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
  },
  selectedTime: {
    backgroundColor: '#ddd',
  },
});

export default App;