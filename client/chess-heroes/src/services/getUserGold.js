import axios from 'axios'

const getUserGold = async (access_token, user_id) => {
    const axiosInstance = axios.create({
        httpsAgent: false,
        validateStatus: () => true
    })

    const response = await axiosInstance.get(
        `https://localhost:3000/user/user/balance/${user_id}`,
        {
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${access_token}`
            }
        }
    )

    if (response.status != 200) {
        throw new Error(response.data.err)  
    }
    
    return response.data.balance
}

export default getUserGold