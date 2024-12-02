import axios from 'axios'

const login = async (username, password) => {
    console.log(username + password)
    const axiosInstance = axios.create({
        // Disable SSL certificate verification
        httpsAgent: false,
        
        // Allow any status code to pass
        validateStatus: () => true
      });
      
      // POST request function
        try {
          const response = await axiosInstance.post(
            'https://localhost:3001/auth/login',
            {
                "username": username,
                "password": password
            },
            {
              headers: {
                'Content-Type': 'application/json'
              }
            }
          )
          console.log(response.data)
      return response.data
    } catch (error) {
        console.error('Error posting user data:', error);
        throw error;
      }
}

export default login