import axios from 'axios'

const getUserCollection = async (user_id, access_token) => {
    const axiosInstance = axios.create({
        httpsAgent: false,
        validateStatus: () => true
    })

    const response = await axiosInstance.get(
        `https://localhost:3000/user/player/collection/${user_id}`,
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
    
    return response.data.collection
}

export default getUserCollection